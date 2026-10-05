import SwiftUI
import SwiftData

struct EditCandidateTaskSheet: View {
    let candidate: CandidateTask
    let meeting: Meeting

    @Environment(\.dismiss) private var dismiss

    @State private var taskDescription: String
    @State private var assignee: AssigneeChoice?
    @State private var members: [RemoteMember] = []
    @State private var hasDueDate: Bool
    @State private var dueDate: Date
    @State private var isSaving = false
    @State private var errorMessage: String?

    init(candidate: CandidateTask, meeting: Meeting) {
        self.candidate = candidate
        self.meeting = meeting
        _taskDescription = State(initialValue: candidate.taskDescription)
        _assignee = State(
            initialValue: candidate.assigneeUserID.map(AssigneeChoice.member)
                ?? candidate.assignee.map { AssigneeChoice.speaker(AssigneePicker.speakerLabel(of: $0)) }
        )
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
                    AssigneePicker(
                        selection: $assignee,
                        members: members,
                        speakers: speakerOptions,
                        currentMemberName: candidate.assigneeName
                    )
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
            .task { members = await AssigneePicker.loadMembers(projectID: meeting.project?.id) }
        }
    }

    private var trimmedDescription: String {
        taskDescription.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// The meeting's speakers. The current one stays selectable even if it's not
    /// among them.
    private var speakerOptions: [String] {
        var labels = AssigneePicker.speakers(of: meeting.sortedAttendees)
        if let current = candidate.assignee.map(AssigneePicker.speakerLabel(of:)),
           !labels.contains(current) {
            labels.insert(current, at: 0)
        }
        return labels
    }

    /// The local speaker attendee for a label, which gives the card its avatar.
    private func speakerAttendee(_ label: String?) -> Attendee? {
        guard let label else { return nil }
        let attendees = meeting.sortedAttendees + [candidate.assignee].compactMap { $0 }
        return attendees.first { AssigneePicker.speakerLabel(of: $0) == label }
    }

    private func save() async {
        isSaving = true
        errorMessage = nil
        defer { isSaving = false }

        if isServerID(candidate.id) {
            do {
                let response = try await MeetingAPIClient.shared.reviewTask(
                    id: candidate.id,
                    action: "edit",
                    title: trimmedDescription,
                    dueDate: hasDueDate ? dueDate : nil,
                    assignee: .some(assignee)
                )
                candidate.taskDescription = response.task.title
                candidate.dueDate = response.task.dueDate.flatMap(LabSyncDate.day(from:))
                candidate.assigneeUserID = response.task.assigneeUserID
                candidate.assigneeName = response.task.assigneeName
                candidate.assignee = speakerAttendee(response.task.ownerLabel)
                dismiss()
            } catch {
                errorMessage = error.localizedDescription
            }
            return
        }

        candidate.taskDescription = trimmedDescription
        candidate.assignee = speakerAttendee(assignee?.speakerLabel)
        candidate.dueDate = hasDueDate ? dueDate : nil
        dismiss()
    }
}

/// Assignee options shared by both edit sheets: project members first
/// ("Will Liu (Me)"), then speakers the diarizer found who aren't members
/// (SPEAKER_1). Only members count toward someone's task summary.
struct AssigneePicker: View {
    @Binding var selection: AssigneeChoice?
    let members: [RemoteMember]
    let speakers: [String]
    /// Shown for the selected member until the member list loads.
    var currentMemberName: String?

    var body: some View {
        Picker("Assignee", selection: $selection) {
            Text("Unassigned").tag(AssigneeChoice?.none)
            if case .member(let id)? = selection, !members.contains(where: { $0.userID == id }) {
                Text(currentMemberName ?? "Project member").tag(selection)
            }
            if !members.isEmpty {
                Section("Project members") {
                    ForEach(members) { member in
                        Text(member.pickerName).tag(AssigneeChoice?.some(.member(member.userID)))
                    }
                }
            }
            if !otherSpeakers.isEmpty {
                Section("Other speakers") {
                    ForEach(otherSpeakers, id: \.self) { label in
                        Text(label).tag(AssigneeChoice?.some(.speaker(label)))
                    }
                }
            }
        }
    }

    /// A speaker recognized by voice is labeled with the member's name, and is
    /// already listed under Project members.
    private var otherSpeakers: [String] {
        speakers.filter { label in
            selection == .speaker(label) || !members.contains { member in
                guard let name = member.displayName else { return false }
                return label == name || label == "\(name) (\(member.email))"
            }
        }
    }

    /// Members can't be listed for local sample projects or while offline.
    static func loadMembers(projectID: String?) async -> [RemoteMember] {
        guard let projectID, isServerID(projectID) else { return [] }
        return (try? await MeetingAPIClient.shared.projectMembers(projectID: projectID)) ?? []
    }

    /// Diarizer labels of a meeting's speakers. UNKNOWN can't own a task.
    static func speakers(of attendees: [Attendee]) -> [String] {
        attendees.map(speakerLabel(of:)).filter { $0.uppercased() != "UNKNOWN" }
    }

    /// Server meetings name each speaker attendee "<meeting id>:<label>".
    /// Sample attendees have no label, so their name stands in.
    static func speakerLabel(of attendee: Attendee) -> String {
        guard let colon = attendee.id.firstIndex(of: ":") else { return attendee.name }
        return String(attendee.id[attendee.id.index(after: colon)...])
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
