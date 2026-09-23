import SwiftUI
import SwiftData

// MeetingDetailView.tsx → the "Session Setup" consent modal.
struct SessionSetupSheet: View {
    let meeting: Meeting

    @Environment(\.dismiss) private var dismiss
    @Query(sort: \Project.createdAt) private var projects: [Project]

    @State private var title: String
    @State private var projectID: String?
    @State private var consentGiven = false

    init(meeting: Meeting) {
        self.meeting = meeting
        _title = State(initialValue: meeting.title)
        _projectID = State(initialValue: meeting.project?.id)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Meeting Title", text: $title)

                    Picker("Project Workspace", selection: $projectID) {
                        Text("None").tag(String?.none)
                        ForEach(projects) { project in
                            Text(project.title).tag(String?.some(project.id))
                        }
                    }
                } header: {
                    Label("EventKit Match", systemImage: "calendar")
                } footer: {
                    Text("Review meeting metadata and confirm consent.")
                }

                Section("Detected Attendees") {
                    ForEach(meeting.sortedAttendees) { attendee in
                        HStack(spacing: 8) {
                            AvatarView(initials: attendee.initials, colorHex: attendee.colorHex, size: 24)
                            Text(attendee.name).font(.subheadline)
                        }
                    }
                }

                Section {
                    Toggle(isOn: $consentGiven) {
                        Text("I confirm all attendees were explicitly notified and consented to this recording.")
                            .font(.subheadline.weight(.medium))
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Session Setup")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Ingest") { ingest() }
                        .disabled(!consentGiven)
                }
            }
        }
    }

    /// The TS button only closed the modal; this saves the edits the form allows.
    private func ingest() {
        meeting.title = title.trimmingCharacters(in: .whitespacesAndNewlines)
        meeting.project = projects.first { $0.id == projectID }
        dismiss()
    }
}

#Preview {
    SessionSetupPreview()
        .modelContainer(PreviewContainer.shared)
}

private struct SessionSetupPreview: View {
    @Query private var meetings: [Meeting]

    var body: some View {
        if let meeting = meetings.first(where: { $0.id == "m1" }) {
            SessionSetupSheet(meeting: meeting)
        }
    }
}
