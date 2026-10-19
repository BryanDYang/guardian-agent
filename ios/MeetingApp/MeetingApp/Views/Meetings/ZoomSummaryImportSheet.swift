import SwiftData
import SwiftUI

struct ZoomSummaryImportSheet: View {
    let project: Project
    var onImported: () -> Void = {}
    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var context
    @State private var title = "Zoom meeting"
    @State private var date = Date()
    @State private var instance = ""
    @State private var summary = ""
    @State private var consent = false
    @State private var isSample = false
    @State private var importing = false
    @State private var error: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Label("Manual summary import", systemImage: "doc.text")
                    Text("Paste an authorized Zoom summary after your meeting. This does not connect your Zoom account or listen to a live call.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                Section("Meeting") {
                    TextField("Title", text: $title)
                    DatePicker("Meeting date", selection: $date, displayedComponents: .date)
                    TextField("Unique meeting instance or test label", text: $instance)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    Text("Use a different label for each meeting, such as solo-test-2026-10-19-1. Reusing a label with the same content avoids duplicate tasks. A recurring meeting ID alone is not enough.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Section("Summary text") {
                    TextEditor(text: $summary)
                        .frame(minHeight: 200)
                        .accessibilityLabel("Zoom summary text")
                    Toggle("This is synthetic test data", isOn: $isSample)
                    Button("Fill Solo Test Example", systemImage: "text.badge.plus") {
                        title = "Zoom solo test"
                        if instance.isEmpty {
                            instance = "solo-test-\(UUID().uuidString.prefix(8))"
                        }
                        summary = "Next steps: Bryan will prepare the evaluation checklist. Bryan will share the demo recording."
                        isSample = true
                    }
                    Text("Summary names need confirmation. Quotes refer to this document, not recorded speech. Review tasks and dates before approving; summary imports do not auto-approve.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                Section {
                    Toggle("I have permission to process this content", isOn: $consent)
                }
                if importing {
                    Section {
                        ProgressView("Extracting tasks from summary…")
                        Text("This may take a minute. If the connection times out, retry with the same instance and unchanged content.")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }
                if let error {
                    Section { Text(error).foregroundStyle(.red) }
                }
            }
            .disabled(importing)
            .navigationTitle("Import Zoom Summary")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }.disabled(importing)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Process") { Task { await process() } }
                        .disabled(importing || !consent || title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || instance.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || summary.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || summary.count > 30_000)
                }
            }
        }
        .interactiveDismissDisabled(importing)
    }

    @MainActor private func process() async {
        importing = true
        error = nil
        defer { importing = false }
        do {
            let remote = try await MeetingAPIClient.shared.importZoomSummary(
                projectID: project.id, title: title, date: date,
                instance: instance, summary: summary, isSample: isSample
            )
            let cached = try context.fetch(FetchDescriptor<Meeting>())
            if !cached.contains(where: { $0.id == remote.id }) {
                let meeting = Meeting(
                    id: remote.id, title: remote.title, date: date,
                    duration: "Summary import", summary: [], suggestions: [],
                    decisions: [], transcript: [], audioFileName: "zoom-summary:no-audio"
                )
                context.insert(meeting)
                meeting.project = project
            }
            try context.save()
            dismiss()
            onImported()
        } catch {
            self.error = error.localizedDescription
        }
    }
}
