import SwiftUI

struct ReturnTaskForReviewSheet: View {
    let taskID: String
    let title: String
    let meetingName: String
    let onReturned: @MainActor () -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var note = ""
    @State private var saving = false
    @State private var error: String?

    var body: some View {
        NavigationStack {
            Form {
                Section { Text(title) }
                Section {
                    TextField("Why does this task need review?", text: $note, axis: .vertical)
                        .lineLimit(3...6)
                } header: { Text("Change note") } footer: {
                    Text("This task will return to \(meetingName) for human review. Pending follow-up emails will stop. The original meeting evidence stays linked.")
                }
                if let error { Text(error).foregroundStyle(.red) }
            }
            .navigationTitle("Return for review")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }.disabled(saving)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(saving ? "Returning…" : "Return") { Task { await submit() } }
                        .disabled(saving || note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || note.count > 1000)
                }
            }
            .interactiveDismissDisabled(saving)
        }
    }

    private func submit() async {
        saving = true
        defer { saving = false }
        do {
            _ = try await MeetingAPIClient.shared.returnTaskForReview(id: taskID, note: note)
            onReturned()
            dismiss()
        } catch { self.error = error.localizedDescription }
    }
}

struct TaskChangesSheet: View {
    let taskID: String
    @Environment(\.dismiss) private var dismiss
    @State private var changes: [RemoteTaskChange] = []
    @State private var loading = true
    @State private var error: String?

    var body: some View {
        NavigationStack {
            List {
                if loading { ProgressView("Loading changes") }
                if let error { Text(error).foregroundStyle(.red) }
                ForEach(changes) { change in
                    VStack(alignment: .leading, spacing: 6) {
                        Text(change.title).font(.headline)
                        Text(change.actorName ?? (change.action == "AUTO_APPROVE" ? "Project automation" : "Project member")).font(.subheadline)
                        if let date = RemoteProject.timestamp(change.createdAt) {
                            Text(date, format: .dateTime.month().day().hour().minute())
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        if let note = change.note { Text(note) }
                    }
                    .padding(.vertical, 4)
                }
                if !loading && changes.isEmpty && error == nil {
                    Text("No changes yet").foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Task changes")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
            .task { await load() }
            .refreshable { await load() }
        }
    }

    private func load() async {
        do {
            changes = try await MeetingAPIClient.shared.taskChanges(id: taskID)
            error = nil
        } catch { self.error = error.localizedDescription }
        loading = false
    }
}
