import AVFoundation
import SwiftUI

@MainActor
@Observable
final class MeetingAudioPlayer {
    private let player = AVPlayer()
    private var fileURL: URL?
    private var pendingSeek: Double?
    private var playAfterSeek = false
    var currentTime: Double = 0
    var duration: Double = 0
    var isPlaying = false
    var isLoading = false
    var error: String?

    func load(meetingID: String) async {
        stop()
        guard isServerID(meetingID) else {
            error = "Audio is unavailable for preview meetings."
            return
        }
        isLoading = true
        error = nil
        do {
            let url = try await MeetingAPIClient.shared.downloadAudio(id: meetingID)
            guard !Task.isCancelled else {
                try? FileManager.default.removeItem(at: url)
                return
            }
            fileURL = url
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio)
            try AVAudioSession.sharedInstance().setActive(true)
            player.replaceCurrentItem(with: AVPlayerItem(url: url))
            while !Task.isCancelled {
                if player.currentItem?.status == .failed {
                    error = "This recording could not be played."
                    break
                }
                if player.currentItem?.status == .readyToPlay {
                    isLoading = false
                    let seconds = player.currentItem?.duration.seconds ?? 0
                    duration = seconds.isFinite ? seconds : 0
                    if duration > 0, let target = pendingSeek {
                        pendingSeek = nil
                        seek(to: target, play: playAfterSeek)
                    }
                    let position = player.currentTime().seconds
                    currentTime = position.isFinite ? position : 0
                    isPlaying = player.rate > 0
                }
                try await Task.sleep(for: .milliseconds(250))
            }
        } catch is CancellationError {
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }

    func pause() {
        player.pause()
        isPlaying = false
        playAfterSeek = false
    }

    func toggle() {
        if player.rate > 0 { player.pause(); isPlaying = false }
        else {
            if duration > 0 && currentTime >= duration - 0.2 { seek(to: 0) }
            player.play()
            isPlaying = true
        }
    }

    func seek(to seconds: Double, play: Bool = false) {
        guard player.currentItem?.status == .readyToPlay else {
            pendingSeek = seconds
            playAfterSeek = play
            return
        }
        let target = min(max(0, seconds), max(0, duration))
        player.seek(to: CMTime(seconds: target, preferredTimescale: 1000),
                    toleranceBefore: .zero, toleranceAfter: .zero)
        currentTime = target
        if play { player.play(); isPlaying = true }
    }

    func stop() {
        player.pause()
        player.replaceCurrentItem(with: nil)
        if let fileURL { try? FileManager.default.removeItem(at: fileURL) }
        fileURL = nil
        currentTime = 0
        duration = 0
        isPlaying = false
    }
}

struct AudioDockView: View {
    let audio: MeetingAudioPlayer
    let retry: () -> Void
    @State private var collapsed = false
    @State private var scrubPosition: Double = 0
    @State private var scrubbing = false

    var body: some View {
        VStack(spacing: 10) {
            if let error = audio.error {
                HStack {
                    Text(error).font(.caption).foregroundStyle(.secondary)
                    Spacer()
                    Button("Retry", action: retry)
                }
            }
            HStack {
                Text("\(time(audio.currentTime)) / \(time(audio.duration))")
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(.secondary)
                Spacer()
                Button { collapsed.toggle() } label: {
                    Image(systemName: collapsed ? "chevron.up" : "chevron.down")
                        .frame(width: 44, height: 44)
                }.accessibilityLabel(collapsed ? "Expand player" : "Collapse player")
            }
            HStack(spacing: 28) {
                Button { audio.seek(to: audio.currentTime - 15) } label: {
                    Image(systemName: "gobackward.15")
                        .font(.system(size: 26, weight: .medium))
                        .frame(width: 56, height: 56)
                }.accessibilityLabel("Back 15 seconds")
                Button { audio.toggle() } label: {
                    Group {
                        if audio.isLoading { ProgressView() }
                        else { Image(systemName: audio.isPlaying ? "pause.fill" : "play.fill") }
                    }
                    .font(.system(size: 32, weight: .semibold))
                    .frame(width: 64, height: 64)
                    .background(Color.accentColor.opacity(0.12), in: Circle())
                }
                .accessibilityLabel(audio.isPlaying ? "Pause recording" : "Play recording")
                Button { audio.seek(to: audio.currentTime + 15) } label: {
                    Image(systemName: "goforward.15")
                        .font(.system(size: 26, weight: .medium))
                        .frame(width: 56, height: 56)
                }.accessibilityLabel("Forward 15 seconds")
            }
            .frame(maxWidth: .infinity)
            .disabled(audio.isLoading || audio.error != nil || audio.duration <= 0)
            if !collapsed {
                Slider(value: Binding(
                    get: { scrubbing ? scrubPosition : audio.currentTime },
                    set: { scrubPosition = $0 }
                ), in: 0...max(audio.duration, 1), onEditingChanged: { editing in
                    if editing { scrubPosition = audio.currentTime }
                    scrubbing = editing
                    if !editing { audio.seek(to: scrubPosition) }
                })
                .disabled(audio.duration <= 0)
                .accessibilityLabel("Recording position")
            }
        }
        .padding(16)
        .background(.regularMaterial)
    }

    private func time(_ seconds: Double) -> String {
        let value = Int(max(0, seconds))
        return String(format: "%d:%02d", value / 60, value % 60)
    }
}
