import SwiftUI
import SwiftData

// MeetingDetailView.tsx → activeSegment === 'transcript'
struct TranscriptSegment: View {
    let meeting: Meeting

    var body: some View {
        if meeting.transcript.isEmpty {
            ContentUnavailableView(
                "No transcript",
                systemImage: "text.bubble",
                description: Text("This session hasn't been transcribed yet.")
            )
            .padding(.top, 48)
        } else {
            VStack(alignment: .leading, spacing: 16) {
                ForEach(meeting.transcript) { turn in
                    turnRow(turn)
                }
            }
        }
    }

    private func turnRow(_ turn: TranscriptTurn) -> some View {
        let speaker = meeting.attendee(withID: turn.speakerID)

        return HStack(alignment: .top, spacing: 8) {
            AvatarView(
                initials: speaker?.initials ?? "?",
                colorHex: speaker?.colorHex ?? "#9CA3AF",
                size: 32
            )

            VStack(alignment: .leading, spacing: 4) {
                HStack(alignment: .firstTextBaseline, spacing: 8) {
                    Text(speaker?.name ?? "Unknown speaker")
                        .font(.caption.weight(.medium))
                        .foregroundStyle(.secondary)
                    Text(turn.startTime)
                        .font(.system(size: 10).monospaced())
                        .foregroundStyle(.tertiary)
                }

                Text(turn.text)
                    .font(.subheadline)
                    .padding(12)
                    .background(
                        RoundedRectangle(cornerRadius: 16)
                            .fill(Color(.systemBackground))
                            .shadow(color: .black.opacity(0.03), radius: 4, y: 1)
                    )
            }

            Spacer(minLength: 0)
        }
    }
}

#Preview {
    TranscriptSegmentPreview()
        .modelContainer(PreviewContainer.shared)
}

private struct TranscriptSegmentPreview: View {
    @Query private var meetings: [Meeting]

    var body: some View {
        ScrollView {
            if let meeting = meetings.first(where: { $0.id == "m1" }) {
                TranscriptSegment(meeting: meeting).padding(16)
            }
        }
        .background(Color(.systemGroupedBackground))
    }
}
