import SwiftUI

/// Onboarding voice sample (also reused from Profile > Speaker Identity to re-record).
/// Frontend placeholder: recording is simulated with a timer and random levels. No microphone
/// access and no upload yet.
struct VoiceEnrollmentView: View {
    let speakerName: String
    var skipTitle = "Skip for now"
    let onFinish: () -> Void
    let onSkip: () -> Void

    private enum Phase {
        case standby
        case recording
        case captured
    }

    private let sampleSeconds = 6.0
    private let ringSize: CGFloat = 112
    private let buttonSize: CGFloat = 84

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var phase: Phase = .standby
    @State private var consentGiven = false
    @State private var elapsed = 0.0
    @State private var level: CGFloat = 0
    @State private var recordingTask: Task<Void, Never>?

    private var progress: Double { min(elapsed / sampleSeconds, 1) }

    /// "Will Liu" reads as "Will", the way someone introduces themselves.
    private var firstName: String {
        speakerName.split(separator: " ").first.map(String.init) ?? speakerName
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 36) {
                intro
                script
                recorder
                    .frame(maxWidth: .infinity)
            }
            .padding(.horizontal, 24)
            .padding(.top, 40)
            .padding(.bottom, 24)
        }
        .scrollBounceBehavior(.basedOnSize)
        .safeAreaInset(edge: .bottom) { footer }
        .background(Color.white)
        .onDisappear { recordingTask?.cancel() }
    }

    // MARK: - Sections

    private var intro: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Set up your voice")
                .font(.largeTitle.bold())
                .foregroundStyle(Palette.ink)
            Text("Read one sentence aloud so your name appears next to what you say in meetings.")
                .font(.body)
                .foregroundStyle(Palette.secondaryText)
        }
    }

    private var script: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("READ ALOUD")
                .font(.caption.weight(.semibold))
                .tracking(1.2)
                .foregroundStyle(Palette.brandBlue)
            Text("\u{201C}Hi, I'm \(firstName). I'm setting up Meeting Memory so it can recognize my voice in our meetings.\u{201D}")
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
    }

    private var recorder: some View {
        VStack(spacing: 16) {
            Button(action: startRecording) {
                ZStack {
                    // Soft halo that breathes with the input level while recording.
                    Circle()
                        .fill(accent.opacity(0.1))
                        .frame(width: ringSize, height: ringSize)
                        .scaleEffect(phase == .recording && !reduceMotion ? 1 + level * 0.22 : 1)
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
            .disabled(!consentGiven || phase != .standby)
            .opacity(consentGiven || phase != .standby ? 1 : 0.35)
            .animation(.easeOut(duration: 0.12), value: level)
            .animation(.easeInOut(duration: 0.25), value: phase)
            .animation(.easeInOut(duration: 0.2), value: consentGiven)
            .accessibilityLabel(recorderLabel)
            .accessibilityValue(phase == .recording ? "\(Int(progress * 100)) percent" : "")

            VStack(spacing: 6) {
                Text(statusText)
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(phase == .captured ? Palette.ink : Palette.secondaryText)
                    .monospacedDigit()

                if phase == .captured {
                    Button("Re-record", action: startRecording)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(Palette.brandBlue)
                        .disabled(!consentGiven)
                }
            }
            .frame(minHeight: 44, alignment: .top)
        }
    }

    private var footer: some View {
        VStack(spacing: 14) {
            consentRow

            Button("Continue", action: onFinish)
                .buttonStyle(PrimaryButtonStyle())
                .disabled(phase != .captured || !consentGiven)

            Button(skipTitle, action: onSkip)
                .font(.subheadline.weight(.medium))
                .foregroundStyle(Palette.secondaryText)
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
                Text("I agree to let Meeting Memory create a voiceprint from this recording.")
                    .font(.footnote)
                    .foregroundStyle(Palette.secondaryText)
                    .multilineTextAlignment(.leading)
                Spacer(minLength: 0)
            }
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(consentGiven ? .isSelected : [])
    }

    // MARK: - State

    private var accent: Color {
        phase == .captured ? Palette.success : Palette.brandBlue
    }

    private var symbol: String {
        switch phase {
        case .standby: "mic.fill"
        case .recording: "waveform"
        case .captured: "checkmark"
        }
    }

    private var statusText: String {
        switch phase {
        case .standby:
            consentGiven ? "Tap to record \u{00B7} \(Int(sampleSeconds)) sec" : "Agree below to start"
        case .recording:
            "Recording \u{00B7} " + String(format: "0:%02d", Int(elapsed))
        case .captured:
            "Sample captured"
        }
    }

    private var recorderLabel: String {
        switch phase {
        case .standby: "Record voice sample"
        case .recording: "Recording"
        case .captured: "Sample captured"
        }
    }

    /// Placeholder for AVAudioRecorder: ticks a timer and feeds random levels into the halo.
    private func startRecording() {
        recordingTask?.cancel()
        elapsed = 0
        level = 0
        phase = .recording

        recordingTask = Task { @MainActor in
            let tick = 0.1
            while elapsed < sampleSeconds {
                try? await Task.sleep(for: .seconds(tick))
                if Task.isCancelled { return }
                elapsed = min(elapsed + tick, sampleSeconds)
                level = CGFloat.random(in: 0.2...1)
            }
            level = 0
            phase = .captured
        }
    }
}

#Preview {
    VoiceEnrollmentView(speakerName: "Will Liu", onFinish: {}, onSkip: {})
}
