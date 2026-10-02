import Foundation

/// Readable text for the backend's invitation error codes (FR-INV-6).
enum InviteErrors {
    static func message(for error: Error) -> String {
        switch error.localizedDescription {
        case "already_member": "You're already in this project."
        case "email_mismatch": "This invite was sent to a different email. Sign in with that email to join."
        case "expired": "This invite has expired. Ask for a new one."
        case "revoked": "This invite was cancelled."
        case "already_used": "This invite has already been used."
        case "Invitation not found": "This invite link isn't valid anymore. Ask for a new one."
        default: error.localizedDescription
        }
    }
}