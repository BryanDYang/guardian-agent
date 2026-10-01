import Foundation
import Observation

/// Frontend-only stand-in for the Supabase-backed session described in
/// "Accounts, Projects & Voice Identity.md". Nothing here talks to a server:
/// each method just moves the UI to the next screen with placeholder data.
@Observable
final class AppSession {
    enum Stage: Equatable {
        case signedOut
        /// New accounts record a voice sample before reaching the tabs.
        case voiceEnrollment
        case signedIn
    }

    var stage: Stage
    var user: PlaceholderUser

    init(stage: Stage = .signedOut, user: PlaceholderUser = .sample) {
        self.stage = stage
        self.user = user
    }

    /// Placeholder: an existing account goes straight to the tabs.
    func logIn(email: String) {
        let handle = email.split(separator: "@").first.map(String.init) ?? email
        user = PlaceholderUser(name: handle, email: email)
        stage = .signedIn
    }

    /// Placeholder: a new account goes to voice enrollment first.
    func signUp(name: String, email: String) {
        user = PlaceholderUser(name: name, email: email, voiceprintEnrolledAt: nil)
        stage = .voiceEnrollment
    }

    /// Placeholder: the real flow learns from Supabase whether the Google account is new.
    func continueWithGoogle(isNewAccount: Bool) {
        user = PlaceholderUser(
            name: PlaceholderUser.sample.name,
            email: PlaceholderUser.sample.email,
            signInMethod: .google,
            voiceprintEnrolledAt: isNewAccount ? nil : .now
        )
        stage = isNewAccount ? .voiceEnrollment : .signedIn
    }

    func finishVoiceEnrollment() {
        user.voiceprintEnrolledAt = .now
        stage = .signedIn
    }

    func skipVoiceEnrollment() {
        stage = .signedIn
    }

    func signOut() {
        user = .sample
        stage = .signedOut
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
