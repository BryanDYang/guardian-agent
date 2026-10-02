import AuthenticationServices
import Foundation
import Observation
import Supabase

/// The app's signed-in state, driven by Supabase Auth. Supabase keeps the
/// session in the Keychain and refreshes it; this class follows its events.
@Observable
final class AppSession {
    enum Stage: Equatable {
        /// Restoring the saved session, or asking /api/v1/me where to go.
        case launching
        case signedOut
        /// Onboarding, in the order /api/v1/me reports it (FR-ONB-1).
        case profileSetup
        case voiceEnrollment
        case signedIn
        /// Signed in, but the backend couldn't be reached.
        case unavailable(String)
    }

    var stage: Stage
    /// Shown in the Profile tab. Name and email come from Supabase; the rest
    /// stays placeholder until the tab reads /api/v1/me (Phase 8).
    var user: PlaceholderUser
    /// Token from an invite link, kept until the user is signed in and has
    /// finished onboarding (FR-ONB-5). Closing the invite sheet clears it.
    var pendingInviteToken: String?

    /// nil in previews, which never talk to Supabase.
    @ObservationIgnored private let auth: AuthClient?

    init(stage: Stage = .launching, user: PlaceholderUser = .sample, auth: AuthClient? = nil) {
        self.stage = stage
        self.user = user
        self.auth = auth
    }

    /// Follows Supabase for the life of the app: the saved session at launch,
    /// log-ins, token refreshes, and sign-outs (including a refresh that failed).
    @MainActor
    func followAuthChanges() async {
        guard let auth else { return }
        for await (_, session) in auth.authStateChanges {
            if let session {
                if stage == .launching || stage == .signedOut {
                    user = PlaceholderUser(supabaseUser: session.user)
                    await loadOnboarding()
                }
            } else {
                stage = .signedOut
            }
        }
    }

    /// Throws Supabase's message, e.g. "Invalid login credentials" or
    /// "Email not confirmed". On success the auth event moves the app on.
    func logIn(email: String, password: String) async throws {
        _ = try await auth?.signIn(email: email, password: password)
    }

    /// Returns true when the email must be confirmed before the first log in.
    func signUp(name: String, email: String, password: String) async throws -> Bool {
        guard let auth else { return false }
        let response = try await auth.signUp(
            email: email,
            password: password,
            data: ["full_name": .string(name)]
        )
        return response.session == nil
    }

    /// Opens Google in a secure browser sheet. Supabase creates the account the
    /// first time it sees this email, or adds Google to the existing account with
    /// the same email. The auth event then moves the app on. Closing the sheet
    /// is not an error.
    func signInWithGoogle() async throws {
        guard let auth else { return }
        do {
            try await auth.signInWithOAuth(
                provider: .google,
                redirectTo: URL(string: "meetingmemory://auth-callback")!
            )
        } catch let error as ASWebAuthenticationSessionError where error.code == .canceledLogin {
            return
        }
    }

    @MainActor
    func signOut() async {
        guard let auth else {
            stage = .signedOut
            return
        }
        do {
            try await auth.signOut()
        } catch {
            // Offline or the server already forgot the session: still forget it here.
            try? await auth.signOut(scope: .local)
        }
    }

    /// Handles meetingmemory://invite?token=... and ignores other links.
    func open(_ url: URL) {
        guard url.scheme == "meetingmemory", url.host() == "invite",
              let token = URLComponents(url: url, resolvingAgainstBaseURL: false)?
                .queryItems?.first(where: { $0.name == "token" })?.value
        else { return }
        pendingInviteToken = token
    }

    /// Asks the backend which onboarding step comes next (FR-ONB-1).
    @MainActor
    func loadOnboarding() async {
        guard auth != nil else { return }
        stage = .launching
        do {
            show(try await MeetingAPIClient.shared.me())
        } catch {
            showFailure(error)
        }
    }

    /// Onboarding step 1. Throws the backend's message for the form to show.
    @MainActor
    func saveProfile(name: String, title: String) async throws {
        guard auth != nil else {
            stage = .voiceEnrollment
            return
        }
        show(try await MeetingAPIClient.shared.updateMe(displayName: name, title: title))
    }

    // The recorder is still a placeholder, so Continue sends "placeholder" and
    // no voice profile is stored (FR-ONB-2a).
    @MainActor
    func finishVoiceEnrollment() async {
        user.voiceprintEnrolledAt = .now
        await completeOnboarding(voiceStep: "placeholder")
    }

    @MainActor
    func skipVoiceEnrollment() async {
        await completeOnboarding(voiceStep: "skipped")
    }

    @MainActor
    private func completeOnboarding(voiceStep: String) async {
        guard auth != nil else {
            stage = .signedIn
            return
        }
        do {
            show(try await MeetingAPIClient.shared.completeOnboarding(voiceStep: voiceStep))
        } catch {
            showFailure(error)
        }
    }

    /// A 401 has already signed the user out, so "Try Again" could never succeed.
    private func showFailure(_ error: Error) {
        if case MeetingAPIError.sessionEnded = error {
            stage = .signedOut
        } else {
            stage = .unavailable(error.localizedDescription)
        }
    }

    /// The server decides the next screen; the app never marks onboarding done itself.
    private func show(_ me: RemoteMe) {
        if let name = me.displayName {
            user.name = name
        }
        user.title = me.title ?? ""
        stage = switch me.onboardingStep {
        case "needs_profile": .profileSetup
        case "needs_voice": .voiceEnrollment
        default: .signedIn
        }
    }
}

struct PlaceholderUser {
    enum SignInMethod {
        case email
        case google
    }

    var name: String
    var email: String
    var title: String = ""
    var signInMethod: SignInMethod = .email
    var voiceprintEnrolledAt: Date? = .now

    var hasVoiceprint: Bool { voiceprintEnrolledAt != nil }
    var initial: String { name.first.map { String($0).uppercased() } ?? "?" }

    static let sample = PlaceholderUser(name: "Alex Rivera", email: "alex@example.com")
}

extension PlaceholderUser {
    /// Name from sign-up ("full_name") or Google ("name"), else the email's first part.
    init(supabaseUser: User) {
        let email = supabaseUser.email ?? ""
        var name = String(email.split(separator: "@").first ?? "You")
        for key in ["full_name", "name"] {
            if case .string(let value)? = supabaseUser.userMetadata[key], !value.isEmpty {
                name = value
                break
            }
        }
        self.init(name: name, email: email, voiceprintEnrolledAt: nil)
    }
}
