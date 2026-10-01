import SwiftUI

/// Onboarding voice sample (also reused from Profile > Speaker Identity to re-record).
/// Frontend placeholder: recording is simulated with a timer and random levels. No microphone
/// access and no upload yet.
struct VoiceEnrollmentView: View {
    let speakerName: String
    var skipTitle = "Skip for now (configure later in Profile)"
    let onFinish: () -> Void
    let onSkip: () -> Void

    private enum Phase {
        case standby
        case recording
        case captured
    }

    private let sampleSeconds = 6.0
    private let barCount = 36

    @State private var phase: Phase = .standby
    @State private var consentGiven = false
    @State private var elapsed = 0.0
    @State private var levels: [CGFloat] = []
    @State private var recordingTask: Task<Void, Never>?

    private var progress: Double { min(elapsed / sampleSeconds, 1) }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                header

                VStack(alignment: .leading, spacing: 8) {
                    Text("Voice Enrollment")
                        .font(.title.bold())
                        .foregroundStyle(Palette.ink)
                    Text("Record a short sample so Meeting Memory can capture your acoustic embeddings and recognize when you speak in meetings.")
                        .font(.subheadline)
                        .foregroundStyle(Palette.secondaryText)
                }

                scriptCard
                recorderCard
                consentCard

                VStack(spacing: 14) {
                    actionButtons
                    Button(skipTitle, action: onSkip)
                        .font(.footnote)
                        .foregroundStyle(Palette.secondaryText)
                }
            }
            .padding(20)
        }
        .background(Color.white)
        .onDisappear { recordingTask?.cancel() }
    }

    // MARK: - Sections

    private var header: some View {
        HStack(spacing: 12) {
            AppMark(size: 44, symbol: "speaker.wave.2.fill")
            VStack(alignment: .leading, spacing: 2) {
                Text("Meeting Memory")
                    .font(.headline)
                    .foregroundStyle(Palette.ink)
                Label("Voice Diarization Setup", systemImage: "sparkles")
                    .font(.caption.weight(.medium))
                    .foregroundStyle(Palette.violet)
            }
            Spacer()
            Text("Step 1 of 1")
                .font(.caption.weight(.semibold))
                .foregroundStyle(Palette.secondaryText)
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(Capsule().fill(Palette.fieldFill))
                .overlay(Capsule().strokeBorder(Palette.border))
        }
    }

    private var scriptCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Label("READ THIS SHORT SCRIPT ALOUD", systemImage: "mic")
                    .font(.caption.weight(.bold))
                    .foregroundStyle(Palette.violet)
                Spacer()
                Text("~\(Int(sampleSeconds)) seconds")
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(Palette.violet)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .overlay(Capsule().strokeBorder(Palette.violet.opacity(0.4)))
            }

            // Placeholder script from the mockup.
            Text("\u{201C}Hi, I'm \(speakerName). I'm calibrating my voice for Meeting Memory to accurately capture action items, diarize meeting turns, and transcribe team decisions.\u{201D}")
                .font(.body.weight(.semibold))
                .italic()
                .foregroundStyle(Palette.ink)
                .padding(16)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 12, style: .continuous).fill(.white))
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .strokeBorder(Palette.violet.opacity(0.15))
                )

            Label("Speak naturally at your standard conversation volume and pace.", systemImage: "info.circle")
                .font(.caption)
                .foregroundStyle(Palette.secondaryText)
        }
        .padding(14)
        .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(Palette.violetWash))
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .strokeBorder(Palette.violet.opacity(0.2))
        )
    }

    private var recorderCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(spacing: 8) {
                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)
                Text(statusText)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.white)
                Spacer()
                Text("\(clock(elapsed)) / \(clock(sampleSeconds))")
                    .font(.system(.caption, design: .monospaced).weight(.semibold))
                    .foregroundStyle(Color.white.opacity(0.6))
            }

            waveform

            VStack(spacing: 6) {
                Capsule()
                    .fill(Color.white.opacity(0.1))
                    .frame(height: 4)
                    .overlay(alignment: .leading) {
                        GeometryReader { geometry in
                            Capsule()
                                .fill(Palette.brandBlue)
                                .frame(width: geometry.size.width * progress)
                        }
                    }
                HStack {
                    Text("Embedding Vector Calibration")
                    Spacer()
                    Text("\(Int(progress * 100))%")
                        .monospacedDigit()
                }
                .font(.caption2)
                .foregroundStyle(Color.white.opacity(0.5))
            }
        }
        .padding(16)
        .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(Palette.ink))
        .accessibilityElement(children: .combine)
    }

    private var waveform: some View {
        HStack(spacing: 3) {
            ForEach(0..<barCount, id: \.self) { index in
                Capsule()
                    .fill(barColor)
                    .frame(width: 3, height: barHeight(at: index))
            }
        }
        .frame(maxWidth: .infinity, minHeight: 56)
        .background(RoundedRectangle(cornerRadius: 10, style: .continuous).fill(Color.white.opacity(0.05)))
        .overlay(
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .strokeBorder(Color.white.opacity(0.08))
        )
        .animation(.easeOut(duration: 0.1), value: levels)
    }

    private var consentCard: some View {
        Button {
            consentGiven.toggle()
        } label: {
            HStack(alignment: .top, spacing: 12) {
                Image(systemName: consentGiven ? "checkmark.square.fill" : "square")
                    .font(.title3)
                    .foregroundStyle(consentGiven ? Palette.brandBlue : Palette.secondaryText)
                Text("I consent to recording my voice to generate biometric diarization embeddings.")
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Palette.ink)
                    .multilineTextAlignment(.leading)
                Spacer(minLength: 0)
            }
            .padding(14)
            .background(RoundedRectangle(cornerRadius: 14, style: .continuous).fill(.white))
            .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).strokeBorder(Palette.border))
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(consentGiven ? .isSelected : [])
    }

    @ViewBuilder
    private var actionButtons: some View {
        switch phase {
        case .standby:
            Button(action: startRecording) {
                Label("Press to Record Voice Sample", systemImage: "mic")
            }
            .buttonStyle(PrimaryButtonStyle())
            .disabled(!consentGiven)

        case .recording:
            Button {} label: {
                Label("Recording...", systemImage: "waveform")
            }
            .buttonStyle(PrimaryButtonStyle())
            .disabled(true)

        case .captured:
            VStack(spacing: 10) {
                Button("Continue", action: onFinish)
                    .buttonStyle(PrimaryButtonStyle())
                    .disabled(!consentGiven)
                Button(action: startRecording) {
                    Label("Re-record", systemImage: "arrow.counterclockwise")
                }
                .buttonStyle(OutlineButtonStyle())
            }
        }
    }

    // MARK: - State

    private var statusText: String {
        switch phase {
        case .standby: "Microphone standby"
        case .recording: "Recording"
        case .captured: "Sample captured"
        }
    }

    private var statusColor: Color {
        switch phase {
        case .standby: Palette.secondaryText
        case .recording: Palette.danger
        case .captured: Palette.success
        }
    }

    private var barColor: Color {
        switch phase {
        case .standby: Color.white.opacity(0.15)
        case .recording: Palette.brandBlue
        case .captured: Palette.success
        }
    }

    private func barHeight(at index: Int) -> CGFloat {
        guard index < levels.count else { return 3 }
        return 3 + levels[index] * 40
    }

    private func clock(_ seconds: Double) -> String {
        let whole = Int(seconds)
        return String(format: "%02d:%02d", whole / 60, whole % 60)
    }

    /// Placeholder for AVAudioRecorder: ticks a timer and feeds random levels into the waveform.
    private func startRecording() {
        recordingTask?.cancel()
        elapsed = 0
        levels = Array(repeating: 0, count: barCount)
        phase = .recording

        recordingTask = Task { @MainActor in
            let tick = 0.1
            while elapsed < sampleSeconds {
                try? await Task.sleep(for: .seconds(tick))
                if Task.isCancelled { return }
                elapsed = min(elapsed + tick, sampleSeconds)
                levels = Array(levels.dropFirst()) + [CGFloat.random(in: 0.15...1)]
            }
            phase = .captured
        }
    }
}

#Preview {
    VoiceEnrollmentView(speakerName: "a", onFinish: {}, onSkip: {})
}
