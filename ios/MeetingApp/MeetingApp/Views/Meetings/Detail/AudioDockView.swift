import SwiftUI

// MeetingDetailView.tsx → the audio scrubber dock.
// Static for now: there is no audio file to play until AddMeetingSheet imports one.
struct AudioDockView: View {
    @State private var isCollapsed = false
    @State private var peaks = (0..<40).map { _ in Double.random(in: 0.2...1.0) }

    var body: some View {
        VStack(spacing: 0) {
            Divider()

            Group {
                if isCollapsed {
                    collapsed
                } else {
                    expanded
                }
            }
            .padding(16)
        }
        .background(.regularMaterial)
    }

    private var collapsed: some View {
        HStack(spacing: 12) {
            playButton(size: 32, glyph: 14)

            Text("14:32")
                .font(.subheadline.weight(.semibold))
            Text("/ 30:40")
                .font(.caption)
                .foregroundStyle(.secondary)

            Spacer()

            Button { isCollapsed = false } label: {
                Image(systemName: "chevron.up")
            }
            .foregroundStyle(.secondary)
        }
    }

    private var expanded: some View {
        VStack(spacing: 12) {
            HStack(spacing: 16) {
                Text("14:32")
                    .font(.caption.monospaced())
                    .foregroundStyle(.secondary)

                WaveformView(peaks: peaks, inactiveColor: Color(.systemGray3))
                    .frame(height: 32)

                Text("-30:40")
                    .font(.caption.monospaced())
                    .foregroundStyle(.secondary)
            }

            HStack {
                Text("1.0x")
                    .font(.caption.weight(.medium))
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 3)
                    .background(RoundedRectangle(cornerRadius: 6).fill(Color(.systemGray6)))

                Spacer()

                HStack(spacing: 24) {
                    Button { } label: {
                        Image(systemName: "gobackward.15").font(.title2)
                    }
                    playButton(size: 48, glyph: 20)
                    Button { } label: {
                        Image(systemName: "goforward.15").font(.title2)
                    }
                }
                .foregroundStyle(.primary)

                Spacer()

                Button { isCollapsed = true } label: {
                    Image(systemName: "chevron.down")
                }
                .foregroundStyle(.secondary)
            }
        }
    }

    private func playButton(size: CGFloat, glyph: CGFloat) -> some View {
        Button { } label: {
            Image(systemName: "play.fill")
                .font(.system(size: glyph))
                .foregroundStyle(Color(.systemBackground))
                .frame(width: size, height: size)
                .background(Circle().fill(Color.primary))
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    VStack {
        Spacer()
        AudioDockView()
    }
    .background(Color(.systemGroupedBackground))
}
