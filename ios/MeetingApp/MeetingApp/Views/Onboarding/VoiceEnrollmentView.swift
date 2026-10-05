import AVFoundation
import SwiftUI

/// Onboarding voice enrollment (also reused from Profile > Speaker Identity to re-record).
/// Records three clips (spec Section 9.1), sends them with the user's consent, and
/// calls `onFinish` once the server has saved the voiceprint.
struct VoiceEnrollmentView: View {
    var skipTitle = "Skip for now"
    let onFinish: () -> Void
    let onSkip: () -> Void

    private enum Phase {
        case standby
        case recording
        case captured
    }

    private struct Clip {
        let label: String
        let heading: String
        let text: String
        let seconds: Double
    }

    /// Two read passages, then one in the user's own words, which sounds more
    /// like how people talk in meetings.
    private static let clips = [
        Clip(
            label: "A",
            heading: "READ ALOUD",
            text: "Thanks for joining today. Before we start, here is a quick update on the project. We finished the first round of testing on Tuesday, and most of the results look good. There are still two open issues with the upload screen, and I would like both of them fixed by the end of next week.",
            seconds: 20
        ),
        Clip(
            label: "B",
            heading: "READ ALOUD",
            text: "Let's go over the action items. Maya will send the budget draft by Thursday, and Jordan will check the numbers for March, April, and May. If anything changes, please post it in the shared channel so everyone sees it before our next meeting.",
            seconds: 20
        ),
        Clip(
            label: "C",
            heading: "IN YOUR OWN WORDS",
            text: "Describe what you worked on last week, or what you plan to do this week.",
            seconds: 20
        ),
    ]

    private let ringSize: CGFloat = 112
    private let buttonSize: CGFloat = 84

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.openURL) private var openURL
    @State private var recorder = ClipRecorder()
    @State private var clipIndex = 0
    @State private var recordings: [URL?] = [nil, nil, nil]
    @State private var phase: Phase = .standby
    @State private var consentGiven = false
    @State private var elapsed = 0.0
    @State private var recordingTask: Task<Void, Never>?
    @State private var isUploading = false
    @State private var microphoneDenied = false
    @State private var errorMessage: String?

    private var clip: Clip { Self.clips[clipIndex] }
    private var isLastClip: Bool { clipIndex == Self.clips.count - 1 }
    private var progress: Double { min(elapsed / clip.seconds, 1) }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 32) {
                intro
                script
                recorderControl
                    .frame(maxWidth: .infinity)
            }
            .padding(.horizontal, 24)
            .padding(.top, 40)
            .padding(.bottom, 24)
        }
        .scrollBounceBehavior(.basedOnSize)
        .safeAreaInset(edge: .bottom) { footer }
        .background(Color.white)
        .onDisappear {
            recordingTask?.cancel()
            recorder.stop()
            deleteRecordings()
        }
    }

    // MARK: - Sections

    private var intro: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Set up your voice")
                .font(.largeTitle.bold())
                .foregroundStyle(Palette.ink)
            Text("Record three short clips so your name appears next to what you say in meetings.")
                .font(.body)
                .foregroundStyle(Palette.secondaryText)
        }
    }

    private var script: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("CLIP \(clipIndex + 1) OF \(Self.clips.count) \u{00B7} \(clip.heading)")
                .font(.caption.weight(.semibold))
                .tracking(1.2)
                .foregroundStyle(Palette.brandBlue)
            Text(clip.label == "C" ? clip.text : "\u{201C}\(clip.text)\u{201D}")
                .font(.title3.weight(.medium))
                .foregroundStyle(Palette.ink)
                .lineSpacing(4)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.leading, 16)
        .overlay(alignment: .leading) {
            Capsule()
                .fill(Palette.brandBlue.opacity(0.25))
                .frame(width: 3)
        }
        .id(clipIndex)
        .transition(.opacity)
    }

    private var recorderControl: some View {
        VStack(spacing: 16) {
            Button(action: toggleRecording) {
                ZStack {
                    // Soft halo that breathes with the microphone level while recording.
                    Circle()
                        .fill(accent.opacity(0.1))
                        .frame(width: ringSize, height: ringSize)
                        .scaleEffect(phase == .recording && !reduceMotion ? 1 + recorder.level * 0.22 : 1)
                    Circle()
                        .stroke(Palette.border, lineWidth: 3)
                        .frame(width: ringSize, height: ringSize)
                    Circle()
                        .trim(from: 0, to: progress)
                        .stroke(accent, style: StrokeStyle(lineWidth: 3, lineCap: .round))
                        .rotationEffect(.degrees(-90))
                        .frame(width: ringSize, height: ringSize)
                        .animation(.linear(duration: 0.1), value: progress)
                    Circle()
                        .fill(accent)
                        .frame(width: buttonSize, height: buttonSize)
                        .shadow(color: accent.opacity(0.3), radius: 12, y: 6)
                    Image(systemName: symbol)
                        .font(.system(size: 30, weight: .semibold))
                        .foregroundStyle(.white)
                        .contentTransition(.symbolEffect(.replace))
                }
                .frame(width: ringSize * 1.3, height: ringSize * 1.3)
                .contentShape(Circle())
            }
            .buttonStyle(.plain)
            .disabled(!consentGiven || phase == .captured || isUploading)
            .opacity(consentGiven || phase != .standby ? 1 : 0.35)
            .animation(.easeOut(duration: 0.12), value: recorder.level)
            .animation(.easeInOut(duration: 0.25), value: phase)
            .animation(.easeInOut(duration: 0.2), value: consentGiven)
            .accessibilityLabel(recorderLabel)
            .accessibilityValue(phase == .recording ? "\(Int(progress * 100)) percent" : "")

            VStack(spacing: 6) {
                Text(statusText)
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(phase == .captured ? Palette.ink : Palette.secondaryText)
                    .monospacedDigit()

                if phase == .captured && !isUploading {
                    Button("Re-record", action: startRecording)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(Palette.brandBlue)
                }

                if microphoneDenied {
                    Button("Allow the microphone in Settings") {
                        if let url = URL(string: UIApplication.openSettingsURLString) {
                            openURL(url)
                        }
                    }
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Palette.brandBlue)
                }

                if let errorMessage {
                    Text(errorMessage)
                        .font(.footnote)
                        .foregroundStyle(Palette.danger)
                        .multilineTextAlignment(.center)
                }
            }
            .frame(minHeight: 44, alignment: .top)
        }
    }

    private var footer: some View {
        VStack(spacing: 14) {
            consentRow

            Button(action: advance) {
                if isUploading {
                    HStack(spacing: 8) {
                        ProgressView().tint(.white)
                        Text("Saving your voiceprint...")
                    }
                } else {
                    Text(isLastClip ? "Finish" : "Next clip")
                }
            }
            .buttonStyle(PrimaryButtonStyle())
            .disabled(phase != .captured || !consentGiven || isUploading)

            Button(skipTitle, action: onSkip)
                .font(.subheadline.weight(.medium))
                .foregroundStyle(Palette.secondaryText)
                .disabled(isUploading)
        }
        .padding(.horizontal, 24)
        .padding(.top, 12)
        .padding(.bottom, 8)
        .background(Color.white)
    }

    private var consentRow: some View {
        Button {
            consentGiven.toggle()
        } label: {
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: consentGiven ? "checkmark.circle.fill" : "circle")
                    .font(.title3)
                    .foregroundStyle(consentGiven ? Palette.brandBlue : Palette.secondaryText.opacity(0.5))
                Text(VoiceConsent.text)
                    .font(.footnote)
                    .foregroundStyle(Palette.secondaryText)
                    .multilineTextAlignment(.leading)
                Spacer(minLength: 0)
            }
        }
        .buttonStyle(.plain)
        .disabled(isUploading)
        .accessibilityAddTraits(consentGiven ? .isSelected : [])
    }

    // MARK: - State

    private var accent: Color {
        phase == .captured ? Palette.success : Palette.brandBlue
    }

    private var symbol: String {
        switch phase {
        case .standby: "mic.fill"
        case .recording: "stop.fill"
        case .captured: "checkmark"
        }
    }

    private var statusText: String {
        switch phase {
        case .standby:
            consentGiven ? "Tap to record \u{00B7} up to \(Int(clip.seconds)) sec" : "Agree below to start"
        case .recording:
            "Recording \u{00B7} " + String(format: "0:%02d", Int(elapsed)) + " \u{00B7} tap to finish"
        case .captured:
            "Clip \(clipIndex + 1) captured"
        }
    }

    private var recorderLabel: String {
        switch phase {
        case .standby: "Record clip \(clipIndex + 1)"
        case .recording: "Finish recording"
        case .captured: "Clip captured"
        }
    }

    // MARK: - Recording

    private func toggleRecording() {
        if phase == .recording {
            finishRecording()
        } else {
            startRecording()
        }
    }

    private func startRecording() {
        recordingTask?.cancel()
        errorMessage = nil
        recordingTask = Task { @MainActor in
            guard await ClipRecorder.requestAccess() else {
                microphoneDenied = true
                return
            }
            microphoneDenied = false
            discardRecording(at: clipIndex)
            let url = FileManager.default.temporaryDirectory
                .appendingPathComponent("voice-\(clip.label)-\(UUID().uuidString).m4a")
            do {
                try recorder.start(to: url)
            } catch {
                errorMessage = "The microphone couldn't start. Try again."
                return
            }
            recordings[clipIndex] = url
            elapsed = 0
            phase = .recording
            let tick = 0.1
            while elapsed < clip.seconds {
                try? await Task.sleep(for: .seconds(tick))
                if Task.isCancelled { return }
                elapsed = min(elapsed + tick, clip.seconds)
            }
            finishRecording()
        }
    }

    private func finishRecording() {
        recordingTask?.cancel()
        recorder.stop()
        phase = .captured
    }

    /// Next clip, or upload all three after the last one.
    private func advance() {
        guard isLastClip else {
            withAnimation(.easeInOut(duration: 0.25)) {
                clipIndex += 1
                phase = recordings[clipIndex] == nil ? .standby : .captured
                elapsed = 0
            }
            return
        }
        Task { await upload() }
    }

    private func upload() async {
        let files = recordings.compactMap { $0 }
        guard files.count == Self.clips.count else { return }
        isUploading = true
        errorMessage = nil
        defer { isUploading = false }
        do {
            _ = try await MeetingAPIClient.shared.grantVoiceConsent(version: VoiceConsent.version)
            _ = try await MeetingAPIClient.shared.enrollVoice(clips: files)
            deleteRecordings()
            onFinish()
        } catch MeetingAPIError.voiceQuality(let failures) {
            // Go back to the first clip that needs recording again.
            let failed = Set(failures.compactMap(\.clip))
            for (index, clip) in Self.clips.enumerated() where failed.contains(clip.label) {
                discardRecording(at: index)
            }
            withAnimation(.easeInOut(duration: 0.25)) {
                clipIndex = Self.clips.firstIndex { failed.contains($0.label) } ?? 0
                phase = recordings[clipIndex] == nil ? .standby : .captured
                elapsed = 0
            }
            errorMessage = failures.first?.message
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    /// Recordings never outlive the screen, whether or not they were sent (D11).
    private func discardRecording(at index: Int) {
        if let url = recordings[index] {
            try? FileManager.default.removeItem(at: url)
        }
        recordings[index] = nil
    }

    private func deleteRecordings() {
        for index in recordings.indices {
            discardRecording(at: index)
        }
    }
}

/// The consent the user agrees to before recording. Bump the version when the
/// wording changes; the server keeps which version each user agreed to (FR-VOICE-1).
enum VoiceConsent {
    static let version = "2026-10"
    static let text = "I agree to let Meeting Memory create a voiceprint from these recordings to label me in my projects' meetings. The recordings are deleted once it's made, and I can delete the voiceprint anytime in Profile."
}

/// Records one clip at a time as AAC, with a live input level for the halo.
@MainActor
@Observable
private final class ClipRecorder {
    private(set) var level: CGFloat = 0
    @ObservationIgnored private var recorder: AVAudioRecorder?
    @ObservationIgnored private var meterTask: Task<Void, Never>?

    /// Asks for the microphone the first time; false if the user said no.
    static func requestAccess() async -> Bool {
        await AVAudioApplication.requestRecordPermission()
    }

    func start(to url: URL) throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.record, mode: .default)
        try session.setActive(true)
        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 48_000,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue,
        ]
        let recorder = try AVAudioRecorder(url: url, settings: settings)
        recorder.isMeteringEnabled = true
        guard recorder.record() else {
            throw CocoaError(.fileWriteUnknown)
        }
        self.recorder = recorder
        meterTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .milliseconds(80))
                self?.updateLevel()
            }
        }
    }

    func stop() {
        meterTask?.cancel()
        meterTask = nil
        recorder?.stop()
        recorder = nil
        level = 0
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }

    /// -50 dB (silence) to 0 dB (loud) becomes 0 to 1.
    private func updateLevel() {
        guard let recorder else { return }
        recorder.updateMeters()
        let decibels = recorder.averagePower(forChannel: 0)
        level = CGFloat(max(0, min(1, (decibels + 50) / 50)))
    }
}

#Preview {
    VoiceEnrollmentView(onFinish: {}, onSkip: {})
}
