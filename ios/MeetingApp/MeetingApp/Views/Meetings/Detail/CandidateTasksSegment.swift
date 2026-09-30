import SwiftUI
import SwiftData

// MeetingDetailView.tsx → activeSegment === 'tasks'
struct CandidateTasksSegment: View {
    let meeting: Meeting
    var loadError: String?
    var retryLoad: () -> Void = {}

    @Environment(\.modelContext) private var context
    @Environment(MeetingNavigator.self) private var navigator
    @Query(sort: \Project.createdAt) private var projects: [Project]
    @Query private var meetings: [Meeting]

    @State private var editingCandidate: CandidateTask?
    @State private var workingID: String?
    @State private var actionError: String?

    var body: some View {
        VStack(spacing: 16) {
            if let loadError {
                Button(loadError, action: retryLoad)
                    .font(.footnote.weight(.semibold))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(RoundedRectangle(cornerRadius: 8).fill(Color.red.opacity(0.1)))
                    .foregroundStyle(.red)
            }

            if let actionError {
                Text(actionError)
                    .font(.footnote)
                    .foregroundStyle(.red)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }

            if candidates.isEmpty && loadError == nil {
                ContentUnavailableView(
                    "No candidate tasks",
                    systemImage: "checklist",
                    description: Text("Nothing was extracted from this session.")
                )
                .padding(.top, 48)
            } else {
                ForEach(candidates) { candidate in
                    card(for: candidate)
                }
            }
        }
        .sheet(item: $editingCandidate) { candidate in
            EditCandidateTaskSheet(candidate: candidate, meeting: meeting)
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
                } else {
                    Label("No due date", systemImage: "calendar.badge.exclamationmark")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 4)
                        .background(
                            RoundedRectangle(cornerRadius: 8).fill(Color(.systemGray6))
                        )
                }

                Button {
                    navigator.pendingSeekMilliseconds = TranscriptTurn.seconds(from: candidate.timestamp) * 1000
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
                let canApprove = candidate.dueDate != nil
                let isWorking = workingID == candidate.id

                Button {
                    Task { await approve(candidate) }
                } label: {
                    Label("Approve", systemImage: "checkmark")
                        .font(.subheadline.weight(.medium))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(
                            RoundedRectangle(cornerRadius: 8)
                                .fill(canApprove ? Color.blue.opacity(0.1) : Color(.systemGray5))
                        )
                }
                .buttonStyle(.plain)
                .foregroundStyle(canApprove ? Color.blue : Color(.systemGray))
                .disabled(!canApprove || isWorking)

                Button {
                    editingCandidate = candidate
                } label: {
                    Label("Edit", systemImage: "pencil")
                        .font(.subheadline.weight(.medium))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(
                            RoundedRectangle(cornerRadius: 8).fill(Color(.systemGray6))
                        )
                }
                .buttonStyle(.plain)
                .foregroundStyle(.primary)

                Button {
                    Task { await dismiss(candidate) }
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
                .disabled(isWorking)
            }

            if candidate.dueDate == nil {
                Text("Add a due date with Edit to approve this task.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
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
    private func approve(_ candidate: CandidateTask) async {
        guard let dueDate = candidate.dueDate else { return }
        if isServerID(candidate.id) {
            await review(candidate, action: "approve", dueDate: dueDate)
            return
        }
        let task = TaskItem(
            id: UUID().uuidString,
            title: candidate.taskDescription,
            state: .open,
            dueDate: dueDate,
            sourceMeetingTitle: meeting.title,
            sourceTimestamp: candidate.timestamp
        )
        context.insert(task)
        task.assignee = candidate.assignee
        task.project = meeting.project
        task.sourceMeeting = meeting
        context.delete(candidate)
    }

    private func dismiss(_ candidate: CandidateTask) async {
        if isServerID(candidate.id) {
            await review(candidate, action: "dismiss", dueDate: nil)
            return
        }
        context.delete(candidate)
    }

    private func review(_ candidate: CandidateTask, action: String, dueDate: Date?) async {
        workingID = candidate.id
        defer { workingID = nil }
        do {
            let response = try await MeetingAPIClient.shared.reviewTask(
                id: candidate.id,
                action: action,
                title: candidate.taskDescription,
                dueDate: dueDate,
                assigneeID: serverAssigneeID(candidate.assignee)
            )
            if action == "approve" {
                let task = try TaskSync.upsert(
                    response.task,
                    projects: projects,
                    meetings: meetings,
                    context: context
                )
                task.assignee = candidate.assignee
                task.project = meeting.project
                task.sourceMeeting = meeting
                task.sourceMeetingTitle = meeting.title
                task.sourceTimestamp = candidate.timestamp
                if let eventKit = response.eventKit {
                    await ReminderScheduler.addReminder(title: eventKit.title, dueDay: eventKit.dueDate)
                }
            }
            context.delete(candidate)
            try context.save()
            actionError = nil
        } catch {
            actionError = error.localizedDescription
        }
    }

    private func serverAssigneeID(_ attendee: Attendee?) -> String? {
        guard let id = attendee?.id, isServerID(id) else { return nil }
        return id
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
