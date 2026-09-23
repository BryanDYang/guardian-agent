import SwiftUI
import SwiftData
import UniformTypeIdentifiers

struct AddMeetingSheet: View {
    let project: Project

    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var context

    @State private var title = "New Sync"
    @State private var date = Date()
    @State private var audioURL: URL?
    @State private var permissionConfirmed = false
    @State private var showFileImporter = false
    @State private var isUploading = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Meeting Title", text: $title)
                    DatePicker("Date", selection: $date, displayedComponents: .date)
                    LabeledContent("Project Workspace", value: project.title)
                } header: {
                    Label("Meeting Details", systemImage: "calendar")
                }

                Section("Audio File") {
                    Button {
                        showFileImporter = true
                    } label: {
                        Label(audioURL?.lastPathComponent ?? "Choose Audio File", systemImage: "waveform")
                    }

                    Button {
                        selectSampleRecording()
                    } label: {
                        Label("Use Sample Recording", systemImage: "doc.badge.plus")
                    }

                    Toggle(
                        "I have permission to process this recording",
                        isOn: $permissionConfirmed
                    )
                }

                if isUploading {
                    Section {
                        HStack {
                            ProgressView()
                            Text("Uploading to the local backend…")
                        }
                    }
                }

                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Add Meeting")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .disabled(isUploading)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Upload") {
                        Task { await uploadMeeting() }
                    }
                    .disabled(!canUpload)
                }
            }
            .fileImporter(isPresented: $showFileImporter, allowedContentTypes: [.audio, .movie]) { result in
                switch result {
                case .success(let url):
                    audioURL = url
                    errorMessage = nil
                case .failure(let error):
                    errorMessage = error.localizedDescription
                }
            }
        }
        .interactiveDismissDisabled(isUploading)
    }

    private var trimmedTitle: String {
        title.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var canUpload: Bool {
        !trimmedTitle.isEmpty
            && audioURL != nil
            && permissionConfirmed
            && !isUploading
    }

    private func selectSampleRecording() {
        guard let sampleURL = Bundle.main.url(
            forResource: "TS3005a-90s-135s",
            withExtension: "wav"
        ) else {
            errorMessage = "The sample recording is missing from the app bundle."
            return
        }

        audioURL = sampleURL
        errorMessage = nil
    }

    @MainActor
    private func uploadMeeting() async {
        guard let audioURL else { return }

        isUploading = true
        errorMessage = nil
        defer { isUploading = false }

        do {
            let remote = try await MeetingAPIClient.shared.upload(
                audioURL: audioURL,
                title: trimmedTitle,
                project: project.title,
                date: date
            )
            let meeting = Meeting(
                id: remote.id,
                title: remote.title,
                date: date,
                duration: "Processing",
                summary: [],
                suggestions: [],
                decisions: [],
                transcript: [],
                audioFileName: audioURL.lastPathComponent,
                processingStatus: remote.status,
                processingError: remote.error
            )
            context.insert(meeting)
            meeting.project = project
            try context.save()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
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
