import SwiftUI
import SwiftData

// main.tsx → app entry point
@main
struct MeetingAppApp: App {
    @State private var navigator = MeetingNavigator()
    @State private var session = AppSession()
    private let container: ModelContainer

    init() {
        do {
            container = try ModelContainer(
                for: Project.self, Meeting.self, Attendee.self, TaskItem.self, CandidateTask.self
            )
            try SeedData.seedIfNeeded(container.mainContext)
        } catch {
            fatalError("Failed to set up the model container: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            Group {
                switch session.stage {
                case .signedOut:
                    AuthFlowView()
                case .voiceEnrollment:
                    VoiceEnrollmentView(
                        speakerName: session.user.name,
                        onFinish: session.finishVoiceEnrollment,
                        onSkip: session.skipVoiceEnrollment
                    )
                case .signedIn:
                    RootTabView()
                }
            }
            .environment(session)
            .environment(navigator)
            // Every sign-in lands on the Meetings tab, not wherever the last user left off.
            .onChange(of: session.stage) { _, stage in
                guard stage == .signedIn else { return }
                navigator.closeMeeting()
                navigator.activeTab = .meetings
            }
        }
        .modelContainer(container)
    }
}