import SwiftUI
import SwiftData

// MeetingDetailView.tsx → activeSegment === 'tasks'
struct CandidateTasksSegment: View {
    let meeting: Meeting
    var onSeek: (Int) -> Void = { _ in }
    var onPause: () -> Void = {}
    var isLoading = false
    var onReviewSpeakers: () -> Void = {}
    var loadError: String?
    var retryLoad: () -> Void = {}

    @Environment(\.modelContext) private var context
    @Environment(MeetingNavigator.self) private var navigator
    @Query(sort: \Project.createdAt) private var projects: [Project]
    @Query private var meetings: [Meeting]

    @State private var reconcilingCandidate: CandidateTask?
    @State private var editingCandidate: CandidateTask?
    @State private var workingID: String?
    @State private var actionError: String?

    var body: some View {
        VStack(spacing: 16) {
            if isServerID(meeting.id) && !meeting.isZoomSummary {
                Button("Review speaker names", systemImage: "person.crop.circle.badge.questionmark", action: onReviewSpeakers)
                    .font(.subheadline.weight(.medium))
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
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

            if isLoading && candidates.isEmpty {
                ProgressView("Loading tasks")
                    .padding(.top, 48)
            } else if candidates.isEmpty && loadError == nil {
                ContentUnavailableView(
                    "No pending tasks",
                    systemImage: "checklist",
                    description: Text("No tasks are awaiting review. Accepted tasks appear in the Tasks tab.")
                )
                .padding(.top, 48)
            } else {
                ForEach(candidates) { candidate in
                    card(for: candidate)
                }
            }
        }
        .sheet(item: $reconcilingCandidate) { candidate in
            ReconcileTaskSheet(candidate: candidate, meeting: meeting, onSeek: onSeek, onPause: onPause) { remote in
                do {
                    try TaskSync.upsert(remote, projects: projects, meetings: meetings, context: context)
                    context.delete(candidate)
                    try context.save()
                } catch { actionError = error.localizedDescription }
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
            if let matchedTitle = matchedTitle(of: candidate) {
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                    Text("Matches an open task from an earlier meeting: \u{201C}\(matchedTitle)\u{201D}. Review whether this is the same task before creating another.")
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
                    initials: candidate.assigneeName.map(initials(of:)) ?? candidate.assignee?.initials ?? "?",
                    colorHex: candidate.assignee?.colorHex ?? "#9CA3AF",
                    size: 24
                )
                Text(candidate.assigneeName ?? candidate.assignee?.name ?? "Unassigned")
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

                if !meeting.isZoomSummary {
                Button {
                    onSeek(TranscriptTurn.seconds(from: candidate.timestamp))
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
            }

            Text(candidate.taskDescription)
                .font(.subheadline.weight(.medium))
                .frame(maxWidth: .infinity, alignment: .leading)

            if !candidate.quote.isEmpty {
                Text("“\(candidate.quote)”")
                    .font(.caption).foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            if candidate.assigneeUserID == nil {
                Button { editingCandidate = candidate } label: {
                    Label(candidate.assignee == nil ? "Confirm owner" : "Connect to an app member", systemImage: "person.crop.circle.badge.questionmark")
                }
                .font(.subheadline.weight(.medium))
                Text(meeting.isZoomSummary ? "Confirm the owner named in this summary. Connect an app member to test follow-up delivery." : candidate.assignee == nil ? "Choose who owns this task. Tap the timestamp to listen here." : "This participant can own a task without an app account. Connect a member only if you know they are the same person.")
                    .font(.caption).foregroundStyle(.secondary)
            }

            if isServerID(candidate.id), candidate.sourceTranscriptID != nil {
                Button("Update an existing task", systemImage: "arrow.triangle.branch") {
                    reconcilingCandidate = candidate
                }
            }

            HStack(spacing: 8) {
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
                                .fill(Color.blue.opacity(0.1))
                        )
                }
                .buttonStyle(.plain)
                .foregroundStyle(Color.blue)
                .disabled(isWorking)

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
                Text("Approve to add to your to-do list. A deadline is optional.")
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
                .strokeBorder(matchedTitle(of: candidate) != nil ? Color.orange.opacity(0.5) : Color(.systemGray5))
        )
    }

    /// From the server's similarity check, or the sample data's duplicate link.
    private func matchedTitle(of candidate: CandidateTask) -> String? {
        candidate.matchedTaskTitle ?? candidate.duplicateOf?.title
    }

    private func initials(of name: String) -> String {
        String(name.split(separator: " ").prefix(2).compactMap(\.first)).uppercased()
    }

    /// Turns the candidate into a real task, then removes it from the review list.
    private func approve(_ candidate: CandidateTask) async {
        let dueDate = candidate.dueDate
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
            sourceTimestamp: meeting.isZoomSummary ? "" : candidate.timestamp
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
                dueDate: dueDate
            )
            if action == "approve" {
                let task = try TaskSync.upsert(
                    response.task,
                    projects: projects,
                    meetings: meetings,
                    context: context
                )
                task.project = meeting.project
                task.sourceMeeting = meeting
                task.sourceMeetingTitle = meeting.title
                task.sourceTimestamp = meeting.isZoomSummary ? "" : candidate.timestamp
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


private struct ReconcileTaskSheet: View {
    let candidate: CandidateTask
    let meeting: Meeting
    let onSeek: (Int) -> Void
    let onPause: () -> Void
    @State private var previewing = false
    let onSaved: (RemoteTask) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var targets: [RemoteTask] = []
    @State private var targetID = ""
    @State private var action = "duplicate"
    @State private var dueDate = Date()
    @State private var confirmed = false
    @State private var error: String?
    @State private var saving = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Evidence from this meeting") {
                    Text(candidate.quote)
                    if !meeting.isZoomSummary {
                    Button("Listen to evidence", systemImage: "play.circle") {
                        let parts = candidate.timestamp.split(separator: ":").compactMap { Int($0) }
                        if parts.count == 2 {
                            previewing = true
                            onSeek(parts[0] * 60 + parts[1])
                        }
                    }
                    }
                }
                    if previewing {
                        Button("Pause audio", systemImage: "pause.circle") {
                            onPause()
                            previewing = false
                        }
                    }
                Section("Existing task") {
                    Picker("Task", selection: $targetID) {
                        Text("Choose a task").tag("")
                        ForEach(targets, id: \.id) { task in Text(task.title).tag(task.id) }
                    }
                    Picker("What changed?", selection: $action) {
                        Text("Same task mentioned again").tag("duplicate")
                        Text("Deadline changed").tag("deadline")
                        Text("Explicitly completed").tag("complete")
                    }
                    if action == "deadline" { DatePicker("Confirmed deadline", selection: $dueDate, displayedComponents: .date) }
                    Toggle("The quoted evidence supports this change", isOn: $confirmed)
                    Text("Nothing changes until you confirm. A similar title alone does not establish a deadline change or completion. Leave unclear cases pending.").font(.footnote).foregroundStyle(.secondary)
                }
                if let error { Text(error).foregroundStyle(.red) }
            }
            .navigationTitle("Review task update")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Confirm") { Task { await save() } }.disabled(!confirmed || targetID.isEmpty || saving)
                }
            }
            .task { await load() }
            .onDisappear { if previewing { onPause() } }
        }
    }

    private func load() async {
        guard let projectID = meeting.project?.id else { return }
        do {
            targets = try await MeetingAPIClient.shared.acceptedTasks(projectID: projectID).filter { $0.meetingID != meeting.id }
            error = nil
        } catch { self.error = error.localizedDescription }
    }

    private func save() async {
        guard let target = targets.first(where: { $0.id == targetID }), let transcriptID = candidate.sourceTranscriptID else { return }
        saving = true
        defer { saving = false }
        do {
            let response = try await MeetingAPIClient.shared.reconcileTask(candidateID: candidate.id, target: target, action: action, dueDate: action == "deadline" ? dueDate : nil, transcriptID: transcriptID, quote: candidate.quote)
            onSaved(response.task)
            dismiss()
        } catch {
            self.error = error.localizedDescription
            await load()
        }
    }
}
