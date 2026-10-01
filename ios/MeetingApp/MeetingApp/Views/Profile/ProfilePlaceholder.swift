import Foundation

/// Placeholder data for the Profile tab until the accounts API exists.
enum ProfilePlaceholder {
    struct Workspace: Identifiable {
        let id = UUID()
        let name: String
        let role: String
        let memberCount: Int
        let lastActivity: String
    }

    struct Invitation: Identifiable {
        let id = UUID()
        let projectName: String
        let invitedBy: String
        let role: String
    }

    struct SpeakerMapping: Identifiable {
        let id = UUID()
        let projectName: String
        let recognizedMeetings: Int
    }

    static let openTasks = 4
    static let overdueTasks = 1
    static let doneTasks = 8

    static let workspaces: [Workspace] = [
        Workspace(name: "Guardian Agent", role: "Owner", memberCount: 4, lastActivity: "2h ago"),
        Workspace(name: "Capstone Research", role: "Member", memberCount: 6, lastActivity: "yesterday"),
        Workspace(name: "Design Sync", role: "Member", memberCount: 3, lastActivity: "3d ago"),
    ]

    static let invitations: [Invitation] = [
        Invitation(projectName: "Q4 Planning", invitedBy: "Jordan Lee", role: "Member"),
    ]

    static let speakerMappings: [SpeakerMapping] = [
        SpeakerMapping(projectName: "Guardian Agent", recognizedMeetings: 6),
        SpeakerMapping(projectName: "Capstone Research", recognizedMeetings: 2),
    ]

    static let termsURL = URL(string: "https://example.com/terms")!
    static let privacyURL = URL(string: "https://example.com/privacy")!
    static let voiceConsentURL = URL(string: "https://example.com/voice-consent")!
    static let supportURL = URL(string: "mailto:support@example.com")!

    static var appVersion: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.0"
    }

    static var buildNumber: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "1"
    }
}
