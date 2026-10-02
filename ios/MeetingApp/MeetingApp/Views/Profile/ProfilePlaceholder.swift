import Foundation

/// Placeholder data for the Profile tab until the accounts API exists.
enum ProfilePlaceholder {
    struct SpeakerMapping: Identifiable {
        let id = UUID()
        let projectName: String
        let recognizedMeetings: Int
    }

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
