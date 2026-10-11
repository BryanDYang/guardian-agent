import SwiftUI
import SwiftData

// MeetingDetailView.tsx → activeSegment === 'storyline'
struct StorylineSegment: View {
    let meeting: Meeting
    var onReviewSpeakers: () -> Void = {}

    @State private var selectedAttendeeID: String?

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 16), count: 3)

    var body: some View {
        if let attendee = selectedAttendee {
            detail(for: attendee)
        } else {
            VStack(alignment: .leading, spacing: 16) {
                if isServerID(meeting.id) {
                    Button("Review speaker names", systemImage: "person.crop.circle.badge.questionmark", action: onReviewSpeakers)
                }
                attendeeGrid
            }
        }
    }

    private var selectedAttendee: Attendee? {
        guard let selectedAttendeeID else { return nil }
        return meeting.attendee(withID: selectedAttendeeID)
    }

    // MARK: Grid

    private var attendeeGrid: some View {
        LazyVGrid(columns: columns, spacing: 16) {
            ForEach(meeting.sortedAttendees) { attendee in
                Button {
                    selectedAttendeeID = attendee.id
                } label: {
                    VStack(spacing: 12) {
                        AvatarView(initials: attendee.initials, colorHex: attendee.colorHex, size: 56)
                        Text(attendee.name)
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(.primary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(16)
                    .background(
                        RoundedRectangle(cornerRadius: 16)
                            .fill(Color(.systemBackground))
                            .shadow(color: .black.opacity(0.03), radius: 4, y: 1)
                    )
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: Attendee detail

    private func detail(for attendee: Attendee) -> some View {
        VStack(alignment: .leading, spacing: 24) {
            Button {
                selectedAttendeeID = nil
            } label: {
                Label("Back to Attendees", systemImage: "chevron.left")
                    .font(.subheadline.weight(.medium))
            }

            HStack(spacing: 12) {
                AvatarView(initials: attendee.initials, colorHex: attendee.colorHex)
                VStack(alignment: .leading, spacing: 2) {
                    Text("\(attendee.name)'s Storyline")
                        .font(.headline)
                    Text("Speaker identified in this meeting")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Divider()

            ContentUnavailableView(
                "Storyline not available",
                systemImage: "text.bubble",
                description: Text("A speaker-specific summary has not been generated. Read their contributions in the Transcript tab.")
            )
        }
    }


}

#Preview {
    StorylineSegmentPreview()
        .modelContainer(PreviewContainer.shared)
}

private struct StorylineSegmentPreview: View {
    @Query private var meetings: [Meeting]

    var body: some View {
        ScrollView {
            if let meeting = meetings.first(where: { $0.id == "m1" }) {
                StorylineSegment(meeting: meeting).padding(16)
            }
        }
        .background(Color(.systemGroupedBackground))
    }
}
