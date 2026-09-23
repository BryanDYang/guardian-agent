import Foundation

// types.ts → ChatMessage (in-memory only, not persisted)
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
    var timestamp: String
}
