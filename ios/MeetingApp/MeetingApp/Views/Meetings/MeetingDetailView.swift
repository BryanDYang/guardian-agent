import SwiftUI
import SwiftData

// MeetingDetailView.tsx → shell: title bar, 4-segment picker, content, audio dock.
struct MeetingDetailView: View {
    let meetingID: String

    @Environment(MeetingNavigator.self) private var navigator
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
                    PrivacySettingsSheet()
                }
                .sheet(isPresented: $showSessionSetup) {
                    SessionSetupSheet(meeting: meeting)
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
}

#Preview {
    NavigationStack {
        MeetingDetailView(meetingID: "m1")
    }
    .environment(MeetingNavigator())
    .modelContainer(PreviewContainer.shared)
}
