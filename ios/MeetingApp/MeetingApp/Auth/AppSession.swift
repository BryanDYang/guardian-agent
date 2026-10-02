import AuthenticationServices
import Foundation
import Observation
import Supabase

/// The app's signed-in state, driven by Supabase Auth. Supabase keeps the
/// session in the Keychain and refreshes it; this class follows its events.
@Observable
final class AppSession {
    enum Stage: Equatable {
        /// Waiting for Supabase to restore a saved session.
        case launching
        case signedOut
        /// New accounts record a voice sample before reaching the tabs (Phase 6).
        case voiceEnrollment
        case signedIn
    }

    var stage: Stage
    /// Shown in the Profile tab. Name and email come from Supabase; the rest
    /// stays placeholder until the tab reads /api/v1/me (Phase 8).
    var user: PlaceholderUser

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
                user = PlaceholderUser(supabaseUser: session.user)
                if stage == .launching || stage == .signedOut {
                    stage = .signedIn
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

    // Placeholders until Phase 6 sends new accounts through voice enrollment.
    func finishVoiceEnrollment() {
        user.voiceprintEnrolledAt = .now
        stage = .signedIn
    }

    func skipVoiceEnrollment() {
        stage = .signedIn
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
