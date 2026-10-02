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

    /// The sheet hangs off the signed-in screen only, so a link opened while
    /// signed out or onboarding waits until the user reaches Meetings (FR-ONB-5).
    private var inviteSheetShown: Binding<Bool> {
        Binding(
            get: { session.pendingInviteToken != nil },
            set: { if !$0 { session.pendingInviteToken = nil } }
        )
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
                        .sheet(isPresented: inviteSheetShown) {
                            if let token = session.pendingInviteToken {
                                InviteLinkSheet(token: token)
                            }
                        }
                }
            }
            .environment(session)
            .environment(navigator)
            .onOpenURL { session.open($0) }
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