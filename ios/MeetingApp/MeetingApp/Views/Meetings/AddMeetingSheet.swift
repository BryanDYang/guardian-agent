import SwiftUI
import SwiftData
import UniformTypeIdentifiers

// MeetingsListView.tsx → the "Add Meeting" modal.
struct AddMeetingSheet: View {
    let project: Project

    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var context

    @State private var title = "New Sync"
    @State private var date = Date()
    @State private var audioFileName: String?
    @State private var showFileImporter = false

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Meeting Title", text: $title)
                    DatePicker("Date", selection: $date, displayedComponents: .date)
                    LabeledContent("Project Workspace", value: project.title)
                } header: {
                    Label("EventKit Match", systemImage: "calendar")
                } footer: {
                    Text("EventKit auto-match found a recent calendar event.")
                }

                Section("Audio File") {
                    Button {
                        showFileImporter = true
                    } label: {
                        Label(audioFileName ?? "Choose Audio File", systemImage: "waveform")
                    }
                }
            }
            .navigationTitle("Add Meeting")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") { addMeeting() }
                        .disabled(trimmedTitle.isEmpty)
                }
            }
            .fileImporter(isPresented: $showFileImporter, allowedContentTypes: [.audio]) { result in
                if case .success(let url) = result {
                    // Only the name is kept. Playback will need the file copied into the app's
                    // documents directory, since this URL isn't accessible later.
                    audioFileName = url.lastPathComponent
                }
            }
        }
    }

    private var trimmedTitle: String {
        title.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func addMeeting() {
        let meeting = Meeting(
            id: UUID().uuidString,
            title: trimmedTitle,
            date: date,
            duration: "0m 00s",
            waveformPeaks: (0..<40).map { _ in Double.random(in: 0.1...0.9) },
            summary: [],
            suggestions: [],
            decisions: [],
            transcript: [],
            audioFileName: audioFileName
        )
        context.insert(meeting)
        meeting.project = project
        dismiss()
    }
}

#Preview {
    AddMeetingPreview()
        .modelContainer(PreviewContainer.shared)
}

private struct AddMeetingPreview: View {
    @Query private var projects: [Project]

    var body: some View {
        if let project = projects.first {
            AddMeetingSheet(project: project)
        }
    }
}
