import AVFoundation
import Observation
import SwiftUI

/// Records meeting audio independently of voiceprint enrollment. Originals remain
/// in Documents/Recordings so a test can be reproduced after upload or failure.
struct MeetingRecordingSheet: View {
    let onUse: (URL, Date) -> Void

    @Environment(\.dismiss) private var dismiss
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.openURL) private var openURL
    @State private var recording = MeetingAudioRecorder()
    @State private var showReplaceConfirmation = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    Image(systemName: recording.isRecording ? "mic.fill" : "waveform")
                        .font(.system(size: 40))
                        .foregroundStyle(recording.isRecording ? Color.red : Color.accentColor)
                        .frame(width: 104, height: 104)
                        .background(.quaternary, in: Circle())
                        .accessibilityHidden(true)

                    VStack(spacing: 8) {
                        Text(recording.isRecording ? "Recording meeting" : recording.url == nil ? "Ready to record" : "Recording saved")
                            .font(.title2.bold())
                        Text(recording.clock)
                            .font(.system(.largeTitle, design: .monospaced).bold())
                            .contentTransition(.numericText())
                            .accessibilityLabel("Duration \(recording.clock)")
                    }

                    if recording.isRecording {
                        ProgressView(value: recording.level)
                            .tint(.red)
                            .accessibilityLabel("Microphone input level")
                        Button {
                            recording.stop()
                        } label: {
                            Label("Stop Recording", systemImage: "stop.fill")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.red)
                        .controlSize(.large)
                    } else if let url = recording.url {
                        VStack(spacing: 14) {
                            Button {
                                recording.togglePlayback()
                            } label: {
                                Label(recording.isPlaying ? "Stop Preview" : "Play Recording",
                                      systemImage: recording.isPlaying ? "stop.fill" : "play.fill")
                                    .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(.bordered)
                            .controlSize(.large)

                            Button {
                                recording.stopPlayback()
                                onUse(url, recording.startedAt ?? .now)
                                dismiss()
                            } label: {
                                Label("Use Recording", systemImage: "checkmark")
                                    .frame(maxWidth: .infinity)
                            }
                            .buttonStyle(.borderedProminent)
                            .controlSize(.large)

                            Button("Record Again", role: .destructive) {
                                showReplaceConfirmation = true
                            }
                        }
                        Text("Saved in this app's Recordings folder in Files. Uploading keeps the original. Closing this screen also keeps it.")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    } else {
                        Button {
                            Task { await recording.start() }
                        } label: {
                            Label(recording.isRequesting ? "Waiting for Microphone…" : "Start Recording", systemImage: "record.circle")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent)
                        .controlSize(.large)
                        .disabled(recording.isRequesting)
                    }

                    if recording.microphoneDenied {
                        Button("Open Microphone Settings") {
                            if let url = URL(string: UIApplication.openSettingsURLString) {
                                openURL(url)
                            }
                        }
                    }
                    if let message = recording.message {
                        Text(message)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    if let error = recording.errorMessage {
                        Text(error)
                            .font(.subheadline)
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                            .accessibilityLabel("Recording error: \(error)")
                    }
                    Text("Keep the app open while recording. Leaving the app stops and saves your audio. Recordings stop automatically after 60 minutes. You can review the clip before uploading it for processing.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding(24)
                .frame(maxWidth: 560)
                .frame(maxWidth: .infinity)
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Record Meeting")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                        .disabled(recording.isRecording || recording.isRequesting)
                }
            }
            .confirmationDialog("Replace this recording?", isPresented: $showReplaceConfirmation, titleVisibility: .visible) {
                Button("Delete Recording and Start Again", role: .destructive) {
                    Task {
                        if recording.discard() { await recording.start() }
                    }
                }
                Button("Cancel", role: .cancel) { }
            } message: {
                Text("This deletes the local take. An uploaded backend copy, if any, is separate.")
            }
        }
        .interactiveDismissDisabled(recording.isRecording || recording.isRequesting)
        .onChange(of: scenePhase) { _, phase in
            if phase != .active {
                recording.stop(reason: "Recording stopped because the app left the foreground.")
                recording.stopPlayback()
            }
        }
        .onReceive(NotificationCenter.default.publisher(for: AVAudioSession.interruptionNotification)) { _ in
            recording.stop(reason: "Audio was interrupted. Review the saved recording before continuing.")
            recording.stopPlayback()
        }
        .onReceive(NotificationCenter.default.publisher(for: AVAudioSession.routeChangeNotification)) { notification in
            if let reason = notification.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt,
               reason == AVAudioSession.RouteChangeReason.oldDeviceUnavailable.rawValue {
                recording.stop(reason: "The audio device disconnected. Review the saved recording.")
                recording.stopPlayback()
            }
        }
        .onDisappear {
            recording.stop()
            recording.stopPlayback()
        }
    }
}

@MainActor
@Observable
final class MeetingAudioRecorder: NSObject, AVAudioRecorderDelegate, AVAudioPlayerDelegate {
    private(set) var isRecording = false
    private(set) var isRequesting = false
    private(set) var isPlaying = false
    private(set) var microphoneDenied = false
    private(set) var elapsed: TimeInterval = 0
    private(set) var level: Double = 0
    private(set) var url: URL?
    private(set) var startedAt: Date?
    private(set) var message: String?
    private(set) var errorMessage: String?

    @ObservationIgnored private var recorder: AVAudioRecorder?
    @ObservationIgnored private var player: AVAudioPlayer?
    @ObservationIgnored private var meterTask: Task<Void, Never>?
    @ObservationIgnored private var pendingURL: URL?

    var clock: String {
        let seconds = Int(elapsed)
        return String(format: "%02d:%02d", seconds / 60, seconds % 60)
    }

    func start() async {
        guard !isRecording, !isRequesting, url == nil else { return }
        isRequesting = true
        errorMessage = nil
        message = nil
        defer { isRequesting = false }
        guard await AVAudioApplication.requestRecordPermission() else {
            microphoneDenied = true
            errorMessage = "Microphone access is off. Enable it in Settings to record a meeting."
            return
        }
        microphoneDenied = false
        guard UIApplication.shared.applicationState == .active else {
            errorMessage = "Return to the app, then tap Start Recording."
            return
        }
        do {
            let directory = try FileManager.default.url(for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
                .appendingPathComponent("Recordings", isDirectory: true)
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true,
                                                   attributes: [.protectionKey: FileProtectionType.completeUnlessOpen])
            var excludedDirectory = directory
            var values = URLResourceValues()
            values.isExcludedFromBackup = true
            try excludedDirectory.setResourceValues(values)
            let began = Date()
            let stamp = began.formatted(.iso8601.year().month().day().time(includingFractionalSeconds: false).timeSeparator(.omitted))
                .replacingOccurrences(of: ":", with: "-")
            let file = directory.appendingPathComponent("Meeting-\(stamp)-\(UUID().uuidString.prefix(8)).m4a")
            pendingURL = file
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker])
            try session.setActive(true)
            let recorder = try AVAudioRecorder(url: file, settings: [
                AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                AVSampleRateKey: 44_100,
                AVNumberOfChannelsKey: 1,
                AVEncoderBitRateKey: 64_000,
                AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue,
            ])
            recorder.delegate = self
            recorder.isMeteringEnabled = true
            guard recorder.prepareToRecord(), recorder.record() else {
                throw CocoaError(.fileWriteUnknown)
            }
            self.recorder = recorder
            startedAt = began
            elapsed = 0
            level = 0
            isRecording = true
            meterTask = Task { [weak self] in
                while !Task.isCancelled {
                    do { try await Task.sleep(for: .milliseconds(100)) }
                    catch { return }
                    guard let self, let recorder = self.recorder, self.isRecording else { return }
                    self.elapsed = recorder.currentTime
                    recorder.updateMeters()
                    self.level = max(0, min(1, (Double(recorder.averagePower(forChannel: 0)) + 50) / 50))
                    if !recorder.isRecording {
                        self.stop(reason: "Recording stopped. Review the saved audio.")
                    } else if self.elapsed >= 3600 {
                        self.stop(reason: "The 60-minute limit was reached. Your recording is saved.")
                    }
                }
            }
        } catch {
            recorder?.stop()
            recorder = nil
            if let pendingURL { try? FileManager.default.removeItem(at: pendingURL) }
            pendingURL = nil
            deactivate()
            errorMessage = "Couldn't start recording: \(error.localizedDescription)"
        }
    }

    func stop(reason: String? = nil) {
        guard isRecording else { return }
        elapsed = max(elapsed, recorder?.currentTime ?? 0)
        isRecording = false
        meterTask?.cancel()
        meterTask = nil
        recorder?.stop()
        recorder = nil
        level = 0
        deactivate()
        guard let file = pendingURL else { return }
        pendingURL = nil
        do {
            let clip = try AVAudioPlayer(contentsOf: file)
            guard clip.duration >= 1 else {
                try FileManager.default.removeItem(at: file)
                elapsed = 0
                errorMessage = "That recording was too short. Record at least one second and try again."
                return
            }
            elapsed = clip.duration
            url = file
            message = reason
        } catch {
            // Preserve unreadable audio for recovery; don't silently erase a take.
            errorMessage = "Couldn't read the saved recording. It remains in Files: \(error.localizedDescription)"
        }
    }

    func togglePlayback() {
        if isPlaying { stopPlayback(); return }
        guard let url else { return }
        errorMessage = nil
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playback, mode: .default)
            try session.setActive(true)
            let player = try AVAudioPlayer(contentsOf: url)
            player.delegate = self
            guard player.play() else { throw CocoaError(.fileReadUnknown) }
            self.player = player
            isPlaying = true
        } catch {
            stopPlayback()
            errorMessage = "Couldn't play the recording: \(error.localizedDescription)"
        }
    }

    func stopPlayback() {
        guard player != nil else { return }
        player?.stop()
        player = nil
        isPlaying = false
        deactivate()
    }

    func discard() -> Bool {
        stopPlayback()
        guard let url else { return true }
        do {
            try FileManager.default.removeItem(at: url)
            self.url = nil
            elapsed = 0
            startedAt = nil
            message = nil
            errorMessage = nil
            return true
        } catch {
            errorMessage = "Couldn't delete the old recording: \(error.localizedDescription)"
            return false
        }
    }

    private func deactivate() {
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }

    nonisolated func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        let finishedID = ObjectIdentifier(recorder)
        Task { @MainActor [weak self] in
            guard let self, self.isRecording,
                  self.recorder.map(ObjectIdentifier.init) == finishedID else { return }
            self.stop(reason: flag ? "Recording finished." : "Recording ended unexpectedly. Check the saved audio.")
        }
    }

    nonisolated func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        let failedID = ObjectIdentifier(recorder)
        Task { @MainActor [weak self] in
            guard let self, self.recorder.map(ObjectIdentifier.init) == failedID else { return }
            self.stop(reason: "Recording was interrupted by an audio error. Check the saved audio.")
        }
    }

    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        let finishedID = ObjectIdentifier(player)
        Task { @MainActor [weak self] in
            guard let self, self.player.map(ObjectIdentifier.init) == finishedID else { return }
            self.stopPlayback()
        }
    }

    nonisolated func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        let failedID = ObjectIdentifier(player)
        Task { @MainActor [weak self] in
            guard let self, self.player.map(ObjectIdentifier.init) == failedID else { return }
            self.stopPlayback()
            self.errorMessage = "Couldn't decode the recording for playback. The original remains in Files."
        }
    }
}
