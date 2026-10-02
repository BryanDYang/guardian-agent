import SwiftUI
import SwiftData
import Supabase

// main.tsx → app entry point
@main
struct MeetingAppApp: App {
    @State private var navigator = MeetingNavigator()
    @State private var session = AppSession(auth: SupabaseService.client.auth)
    private let container: ModelContainer

    init() {
        do {
            container = try ModelContainer(
                for: Project.self, Meeting.self, Attendee.self, TaskItem.self, CandidateTask.self
            )
            try ProjectSync.prepareCache(context: container.mainContext)
        } catch {
            fatalError("Failed to set up the model container: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            Group {
                switch session.stage {
                case .launching:
                    // Brief: Supabase is reading the saved session from the Keychain.
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                case .signedOut:
                    AuthFlowView()
                case .profileSetup:
                    ProfileSetupView()
                case .voiceEnrollment:
                    VoiceEnrollmentView(
                        speakerName: session.user.name,
                        onFinish: { Task { await session.finishVoiceEnrollment() } },
                        onSkip: { Task { await session.skipVoiceEnrollment() } }
                    )
                case .unavailable(let message):
                    ContentUnavailableView {
                        Label("Can't reach Meeting Memory", systemImage: "wifi.exclamationmark")
                    } description: {
                        Text(message)
                    } actions: {
                        Button("Try Again") { Task { await session.loadOnboarding() } }
                        Button("Sign Out") { Task { await session.signOut() } }
                    }
                case .signedIn:
                    RootTabView()
                }
            }
            .environment(session)
            .environment(navigator)
            .task { await session.followAuthChanges() }
            .onChange(of: session.stage) { _, stage in
                switch stage {
                case .signedIn:
                    // Every sign-in lands on the Meetings tab, not wherever the last user left off.
                    navigator.closeMeeting()
                    navigator.activeTab = .meetings
                case .signedOut:
                    LocalCache.clear(container.mainContext)
                default:
                    break
                }
            }
        }
        .modelContainer(container)
    }
}