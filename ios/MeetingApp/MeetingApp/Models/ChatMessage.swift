import Foundation

// types.ts → ChatMessage (the thread itself is stored on the server)
struct ChatMessage: Identifiable {
    enum Role {
        case user
        case assistant
    }

    var id: String
    var role: Role
    var content: String
    var citations: [Citation] = []
}

// types.ts → Citation
struct Citation: Identifiable {
    var id: String
    var meetingId: String
    var meetingTitle: String
    /// Display time ("12:04"); empty when the source has no time (a summary).
    var timestamp: String
    /// Where the audio should start for this citation.
    var startTimeMilliseconds: Int? = nil
    var quote: String? = nil
}

extension ChatMessage {
    init(remote: RemoteChatMessage) {
        self.init(
            id: remote.id,
            role: remote.role == "user" ? .user : .assistant,
            content: remote.content,
            citations: (remote.citations ?? []).map { citation in
                Citation(
                    id: "\(remote.id)-\(citation.number)",
                    meetingId: citation.meetingID,
                    meetingTitle: citation.meetingName,
                    timestamp: citation.startTimeMilliseconds.map(ChatMessage.clock) ?? "",
                    startTimeMilliseconds: citation.startTimeMilliseconds,
                    quote: citation.quote
                )
            }
        )
    }

    /// Same format as the backend prompt: "mm:ss", or "h:mm:ss" past an hour.
    static func clock(_ milliseconds: Int) -> String {
        let seconds = milliseconds / 1000
        let (hours, minutes, rest) = (seconds / 3600, seconds % 3600 / 60, seconds % 60)
        return hours > 0
            ? String(format: "%d:%02d:%02d", hours, minutes, rest)
            : String(format: "%02d:%02d", minutes, rest)
    }
}