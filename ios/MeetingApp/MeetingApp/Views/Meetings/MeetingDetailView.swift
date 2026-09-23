import SwiftUI
import SwiftData

// MeetingDetailView.tsx → shell: title bar, 4-segment picker, content, audio dock.
struct MeetingDetailView: View {
    let meetingID: String

    @Environment(MeetingNavigator.self) private var navigator
    @Environment(\.modelContext) private var context
    @Query private var meetings: [Meeting]

    @State private var showPrivacySettings = false
    @State private var showSessionSetup = false

    var body: some View {
        @Bindable var navigator = navigator

        Group {
            if let meeting {
                VStack(spacing: 0) {
                    Picker("Segment", selection: $navigator.activeSegment) {
                        ForEach(MeetingSegment.allCases) { segment in
                            Text(segment.title).tag(segment)
                        }
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)

                    if (meeting.processingStatus ?? "completed") != "completed" {
                        ProcessingStatusView(
                            status: meeting.processingStatus ?? "completed",
                            error: meeting.processingError,
                            retry: { Task { await retry(meeting) } }
                        )
                        .padding(.horizontal, 16)
                    }

                    ScrollView {
                        segmentContent(for: meeting)
                            .padding(16)
                    }

                    AudioDockView()
                }
                .background(Color(.systemGroupedBackground))
                .navigationTitle(meeting.title)
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItemGroup(placement: .topBarTrailing) {
                        Button { showPrivacySettings = true } label: {
                            Image(systemName: "gearshape")
                        }
                        ShareLink(item: shareText(for: meeting)) {
                            Image(systemName: "square.and.arrow.up")
                        }
                    }
                }
                .sheet(isPresented: $showPrivacySettings) {
                    PrivacySettingsSheet(project: meeting.project)
                }
                .sheet(isPresented: $showSessionSetup) {
                    SessionSetupSheet(meeting: meeting)
                }
                .task(id: meeting.id) {
                    await poll(meeting)
                }
            } else {
                ContentUnavailableView("Meeting not found", systemImage: "waveform.slash")
            }
        }
    }

    private var meeting: Meeting? {
        meetings.first { $0.id == meetingID }
    }

    @ViewBuilder
    private func segmentContent(for meeting: Meeting) -> some View {
        switch navigator.activeSegment {
        case .summary:
            SummarySegment(meeting: meeting)
        case .tasks:
            CandidateTasksSegment(meeting: meeting)
        case .transcript:
            TranscriptSegment(meeting: meeting)
        case .storyline:
            StorylineSegment(meeting: meeting)
        }
    }

    private func shareText(for meeting: Meeting) -> String {
        ([meeting.title] + meeting.summary).joined(separator: "\n")
    }

    @MainActor
    private func poll(_ meeting: Meeting) async {
        while !Task.isCancelled && ["queued", "transcribing", "extracting"].contains(meeting.processingStatus ?? "completed") {
            do {
                let remote = try await MeetingAPIClient.shared.meeting(id: meeting.id)
                try RemoteMeetingApplier.apply(remote, to: meeting, context: context)
                if remote.status == "completed" || remote.status == "failed" {
                    return
                }
                try await Task.sleep(for: .seconds(2))
            } catch is CancellationError {
                return
            } catch {
                meeting.processingError = error.localizedDescription
                return
            }
        }
    }

    @MainActor
    private func retry(_ meeting: Meeting) async {
        do {
            let remote = try await MeetingAPIClient.shared.retry(id: meeting.id)
            try RemoteMeetingApplier.apply(remote, to: meeting, context: context)
            await poll(meeting)
        } catch {
            meeting.processingError = error.localizedDescription
        }
    }
}

private struct ProcessingStatusView: View {
    let status: String
    let error: String?
    let retry: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            if status == "failed" {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.red)
            } else {
                ProgressView()
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(statusLabel)
                    .font(.subheadline.weight(.semibold))
                if let error {
                    Text(error)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()

            if status == "failed" {
                Button("Retry", action: retry)
                    .buttonStyle(.bordered)
            }
        }
        .padding(12)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
    }

    private var statusLabel: LocalizedStringResource {
        switch status {
        case "queued": "Queued"
        case "transcribing": "Transcribing audio"
        case "extracting": "Extracting meeting details"
        case "failed": "Processing failed"
        default: "Connecting to backend"
        }
    }
}

#Preview {
    NavigationStack {
        MeetingDetailView(meetingID: "m1")
    }
    .environment(MeetingNavigator())
    .modelContainer(PreviewContainer.shared)
}
