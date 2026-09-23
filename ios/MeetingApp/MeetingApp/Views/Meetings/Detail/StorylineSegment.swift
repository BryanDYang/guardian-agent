import SwiftUI
import SwiftData

// MeetingDetailView.tsx → activeSegment === 'storyline'
struct StorylineSegment: View {
    let meeting: Meeting

    @State private var selectedAttendeeID: String?

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 16), count: 3)

    var body: some View {
        if let attendee = selectedAttendee {
            detail(for: attendee)
        } else {
            attendeeGrid
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
                    Text("Extracted perspective and intent")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Divider()

            VStack(spacing: 16) {
                perspectiveCard(
                    title: "WHAT THEY WANT",
                    tint: .blue,
                    text: "Looking to streamline the current hardware integration process and reduce friction between the firmware updates and physical testing phases."
                )
                perspectiveCard(
                    title: "WHAT THEY SEE",
                    tint: .green,
                    text: "Noticing that current blockages are mainly due to misaligned expectations on delivery timelines for the prototype parts."
                )
                perspectiveCard(
                    title: "TALKING ABOUT",
                    tint: .purple,
                    text: "Focused heavily on establishing a stricter milestone schedule and acquiring the new v3 sensory modules before next month."
                )
            }
        }
    }

    private func perspectiveCard(title: String, tint: Color, text: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.caption.weight(.bold))
                .kerning(0.5)
                .foregroundStyle(tint)
            Text(text)
                .font(.subheadline)
                .foregroundStyle(.primary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(tint.opacity(0.08))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(tint.opacity(0.2))
        )
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
