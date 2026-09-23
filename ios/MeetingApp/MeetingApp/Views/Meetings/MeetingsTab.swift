import SwiftUI
import SwiftData

/// The two things this stack can push.
enum MeetingsRoute: Hashable {
    case project(String)
    case meeting(String)
}

// MeetingsTab.tsx → NavigationStack instead of a manual show/hide overlay.
struct MeetingsTab: View {
    @Environment(MeetingNavigator.self) private var navigator
    @State private var path: [MeetingsRoute] = []

    var body: some View {
        NavigationStack(path: $path) {
            MeetingsListView(projectID: nil)
                .navigationDestination(for: MeetingsRoute.self) { route in
                    switch route {
                    case .project(let id):
                        MeetingsListView(projectID: id)
                    case .meeting(let id):
                        MeetingDetailView(meetingID: id)
                    }
                }
        }
        // A citation tap in Chat sets selectedMeetingID; push it.
        .onChange(of: navigator.selectedMeetingID) { _, meetingID in
            syncPath(with: meetingID)
        }
        // Swipe-back or the back button pops the stack; mirror that onto the navigator.
        .onChange(of: path) { _, newPath in
            if case .meeting(let id) = newPath.last {
                navigator.selectedMeetingID = id
            } else {
                navigator.selectedMeetingID = nil
            }
        }
        .onAppear {
            syncPath(with: navigator.selectedMeetingID)
        }
    }

    private func syncPath(with meetingID: String?) {
        guard let meetingID else {
            if case .meeting = path.last { path.removeLast() }
            return
        }
        if path.last != .meeting(meetingID) {
            path.append(.meeting(meetingID))
        }
    }
}

#Preview {
    MeetingsTab()
        .environment(MeetingNavigator())
        .modelContainer(PreviewContainer.shared)
}
