import SwiftUI
import SwiftData

// MeetingDetailView.tsx → activeSegment === 'tasks'
struct CandidateTasksSegment: View {
    let meeting: Meeting

    @Environment(\.modelContext) private var context
    @Environment(MeetingNavigator.self) private var navigator

    var body: some View {
        if candidates.isEmpty {
            ContentUnavailableView(
                "No candidate tasks",
                systemImage: "checklist",
                description: Text("Nothing was extracted from this session.")
            )
            .padding(.top, 48)
        } else {
            VStack(spacing: 16) {
                ForEach(candidates) { candidate in
                    card(for: candidate)
                }
            }
        }
    }

    private var candidates: [CandidateTask] {
        meeting.candidateTasks.sorted { $0.timestamp < $1.timestamp }
    }

    private func card(for candidate: CandidateTask) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            if candidate.duplicateOf != nil {
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                    Text("Matches Open Task from Prev Sync. Update existing status or track as new?")
                }
                .font(.caption)
                .padding(10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(Color.orange.opacity(0.12))
                )
            }

            HStack(spacing: 8) {
                AvatarView(
                    initials: candidate.assignee?.initials ?? "?",
                    colorHex: candidate.assignee?.colorHex ?? "#9CA3AF",
                    size: 24
                )
                Text(candidate.assignee?.name ?? "Unassigned")
                    .font(.subheadline.weight(.medium))

                Spacer(minLength: 8)

                if let dueDate = candidate.dueDate {
                    Label(
                        "Due \(dueDate.formatted(.dateTime.month(.abbreviated).day()))",
                        systemImage: "calendar"
                    )
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.red)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 4)
                    .background(
                        RoundedRectangle(cornerRadius: 8).fill(Color.red.opacity(0.1))
                    )
                }

                Button {
                    navigator.activeSegment = .transcript
                } label: {
                    Text("[\(candidate.timestamp)]")
                        .font(.caption.monospaced())
                        .padding(.horizontal, 6)
                        .padding(.vertical, 4)
                        .background(
                            RoundedRectangle(cornerRadius: 6).fill(Color.blue.opacity(0.1))
                        )
                }
                .buttonStyle(.plain)
                .foregroundStyle(.blue)
            }

            Text(candidate.taskDescription)
                .font(.subheadline.weight(.medium))
                .frame(maxWidth: .infinity, alignment: .leading)

            HStack(spacing: 8) {
                Button {
                    approve(candidate)
                } label: {
                    Label("Approve", systemImage: "checkmark")
                        .font(.subheadline.weight(.medium))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(
                            RoundedRectangle(cornerRadius: 8).fill(Color.blue.opacity(0.1))
                        )
                }
                .buttonStyle(.plain)
                .foregroundStyle(.blue)

                Button {
                    context.delete(candidate)
                } label: {
                    Label("Dismiss", systemImage: "xmark")
                        .font(.subheadline.weight(.medium))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(
                            RoundedRectangle(cornerRadius: 8).fill(Color(.systemGray6))
                        )
                }
                .buttonStyle(.plain)
                .foregroundStyle(.red)
            }
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.03), radius: 4, y: 1)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(candidate.duplicateOf != nil ? Color.orange.opacity(0.5) : Color(.systemGray5))
        )
    }

    /// Turns the candidate into a real task, then removes it from the review list.
    private func approve(_ candidate: CandidateTask) {
        let task = TaskItem(
            id: UUID().uuidString,
            title: candidate.taskDescription,
            state: .open,
            dueDate: candidate.dueDate,
            sourceMeetingTitle: meeting.title,
            sourceTimestamp: candidate.timestamp
        )
        context.insert(task)
        task.assignee = candidate.assignee
        task.project = meeting.project
        task.sourceMeeting = meeting

        context.delete(candidate)
    }
}

#Preview {
    CandidateTasksPreview()
        .environment(MeetingNavigator())
        .modelContainer(PreviewContainer.shared)
}

private struct CandidateTasksPreview: View {
    @Query private var meetings: [Meeting]

    var body: some View {
        ScrollView {
            if let meeting = meetings.first(where: { $0.id == "m1" }) {
                CandidateTasksSegment(meeting: meeting).padding(16)
            }
        }
        .background(Color(.systemGroupedBackground))
    }
}
