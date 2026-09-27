import SwiftUI
import SwiftData

struct EditCandidateTaskSheet: View {
    let candidate: CandidateTask
    let meeting: Meeting

    @Environment(\.dismiss) private var dismiss

    @State private var taskDescription: String
    @State private var assigneeID: String?
    @State private var hasDueDate: Bool
    @State private var dueDate: Date
    @State private var isSaving = false
    @State private var errorMessage: String?

    init(candidate: CandidateTask, meeting: Meeting) {
        self.candidate = candidate
        self.meeting = meeting
        _taskDescription = State(initialValue: candidate.taskDescription)
        _assigneeID = State(initialValue: candidate.assignee?.id)
        _hasDueDate = State(initialValue: candidate.dueDate != nil)
        _dueDate = State(initialValue: candidate.dueDate ?? Calendar.current.startOfDay(for: Date()))
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Task") {
                    TextField("Task description", text: $taskDescription, axis: .vertical)
                        .lineLimit(2...6)
                }

                Section("Assignee") {
                    Picker("Assignee", selection: $assigneeID) {
                        Text("Unassigned").tag(String?.none)
                        ForEach(assigneeOptions) { attendee in
                            Text(attendee.name).tag(String?.some(attendee.id))
                        }
                    }
                }

                Section {
                    Toggle("Due date", isOn: $hasDueDate.animation())
                    if hasDueDate {
                        DatePicker("Date", selection: $dueDate, displayedComponents: .date)
                    }
                } header: {
                    Text("Due Date")
                } footer: {
                    if !hasDueDate {
                        Text("A due date is required before this task can be approved.")
                    }
                }

                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Edit Task")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .disabled(isSaving)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { Task { await save() } }
                        .disabled(trimmedDescription.isEmpty || isSaving)
                }
            }
        }
    }

    private var trimmedDescription: String {
        taskDescription.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// The current assignee may not be one of the meeting's attendees, so keep them selectable.
    private var assigneeOptions: [Attendee] {
        var options = meeting.sortedAttendees
        if let current = candidate.assignee, !options.contains(where: { $0.id == current.id }) {
            options.insert(current, at: 0)
        }
        return options
    }

    private func save() async {
        isSaving = true
        errorMessage = nil
        defer { isSaving = false }

        let assignee = assigneeOptions.first { $0.id == assigneeID }
        if isServerID(candidate.id) {
            do {
                let response = try await MeetingAPIClient.shared.reviewTask(
                    id: candidate.id,
                    action: "edit",
                    title: trimmedDescription,
                    dueDate: hasDueDate ? dueDate : nil,
                    assigneeID: assignee.flatMap { isServerID($0.id) ? $0.id : nil }
                )
                candidate.taskDescription = response.task.title
                candidate.dueDate = response.task.dueDate.flatMap(LabSyncDate.day(from:))
                candidate.assignee = assignee
                dismiss()
            } catch {
                errorMessage = error.localizedDescription
            }
            return
        }

        candidate.taskDescription = trimmedDescription
        candidate.assignee = assignee
        candidate.dueDate = hasDueDate ? dueDate : nil
        dismiss()
    }
}

#Preview {
    EditCandidateTaskPreview()
        .modelContainer(PreviewContainer.shared)
}

private struct EditCandidateTaskPreview: View {
    @Query private var meetings: [Meeting]

    var body: some View {
        if let meeting = meetings.first(where: { $0.id == "m1" }),
           let candidate = meeting.candidateTasks.first {
            EditCandidateTaskSheet(candidate: candidate, meeting: meeting)
        }
    }
}
