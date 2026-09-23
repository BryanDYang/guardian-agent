import SwiftUI
import SwiftData

struct PrivacySettingsSheet: View {
    let project: Project?

    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var context

    @State private var showPurgeConfirmation = false
    @State private var isPurging = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Button("Open Redaction Tool") { }
                } header: {
                    Text("Selective Redaction")
                } footer: {
                    Text("Select sensitive transcript segments to permanently remove from future indexing.")
                }

                Section {
                    Button("Purge Project Data", role: .destructive) {
                        showPurgeConfirmation = true
                    }
                    .disabled(project == nil || isPurging)

                    if isPurging {
                        ProgressView("Purging project data…")
                    }

                    if let errorMessage {
                        Text(errorMessage)
                            .foregroundStyle(.red)
                    }
                } header: {
                    Text("Project-Scoped Purge")
                        .foregroundStyle(.red)
                } footer: {
                    Text("Deletes this project's meetings, transcripts, extracted results, tasks, and backend audio. The project remains available for another test.")
                }
            }
            .navigationTitle("Privacy & Governance")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                        .disabled(isPurging)
                }
            }
            .confirmationDialog(
                "Purge all data for \(project?.title ?? "this project")?",
                isPresented: $showPurgeConfirmation,
                titleVisibility: .visible
            ) {
                Button("Purge Project Data", role: .destructive) {
                    Task { await purgeProject() }
                }
                Button("Cancel", role: .cancel) { }
            } message: {
                Text("This permanently deletes local and backend meeting data and cannot be undone.")
            }
        }
        .interactiveDismissDisabled(isPurging)
        .presentationDetents([.medium, .large])
    }

    @MainActor
    private func purgeProject() async {
        guard let project else { return }

        isPurging = true
        errorMessage = nil
        defer { isPurging = false }

        do {
            _ = try await MeetingAPIClient.shared.purgeProject(named: project.title)

            let meetings = project.meetings
            for task in project.tasks {
                context.delete(task)
            }
            for meeting in meetings {
                for attendee in meeting.attendees where attendee.id.hasPrefix("\(meeting.id):") {
                    context.delete(attendee)
                }
                context.delete(meeting)
            }
            try context.save()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    PrivacySettingsSheet(project: nil)
}
