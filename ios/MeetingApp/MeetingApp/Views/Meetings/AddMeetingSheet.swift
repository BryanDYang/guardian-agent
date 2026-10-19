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
    @State private var showRecorder = false
    @State private var showZoomImport = false
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

                Section {
                    Toggle(
                        "Everyone has agreed to recording and processing",
                        isOn: $permissionConfirmed
                    )

                    Button {
                        showRecorder = true
                    } label: {
                        Label("Record Audio", systemImage: "mic.circle.fill")
                    }
                    .disabled(!permissionConfirmed)

                    Button {
                        showFileImporter = true
                    } label: {
                        Label("Import Audio File", systemImage: "folder")
                    }

                    Button {
                        selectSampleRecording()
                    } label: {
                        Label("Use Sample Recording", systemImage: "doc.badge.plus")
                    }

                    if let audioURL {
                        Label(audioURL.lastPathComponent, systemImage: "waveform")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .lineLimit(2)
                    }
                } header: {
                    Text("Meeting Audio")
                } footer: {
                    Text("Confirm everyone's permission before recording. Record in the app or choose an existing file, then upload to generate the transcript and tasks.")
                }

                Section {
                    Button("Import Zoom Summary", systemImage: "doc.text") {
                        showZoomImport = true
                    }
                } footer: {
                    Text("Already have a Zoom summary? Import it directly to review tasks without reprocessing audio.")
                }

                if isUploading {
                    Section {
                        HStack {
                            ProgressView()
                            Text("Uploading for processing…")
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
            .disabled(isUploading)
            .navigationTitle("Add Meeting")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .disabled(isUploading)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Upload & Process") {
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
            .sheet(isPresented: $showRecorder) {
                MeetingRecordingSheet { url, recordedAt in
                    audioURL = url
                    date = recordedAt
                    errorMessage = nil
                    if title == "New Sync" {
                        title = "Recording \(recordedAt.formatted(date: .abbreviated, time: .shortened))"
                    }
                }
            }
            .sheet(isPresented: $showZoomImport) {
                ZoomSummaryImportSheet(project: project) { dismiss() }
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
                projectID: project.id,
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
