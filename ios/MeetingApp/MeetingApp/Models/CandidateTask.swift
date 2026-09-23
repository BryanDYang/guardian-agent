import Foundation
import SwiftData

// types.ts → CandidateTask
@Model
final class CandidateTask {
    @Attribute(.unique) var id: String
    /// Was `description`. That name is reserved by Core Data, which backs SwiftData.
    var taskDescription: String
    var quote: String
    var timestamp: String
    var dueDate: Date?

    // Relationships — set after insert.
    var assignee: Attendee?
    /// Replaces `duplicateOf?: string` (id of an existing task).
    var duplicateOf: TaskItem?
    /// Owning meeting. Inverse declared on Meeting.candidateTasks.
    var meeting: Meeting?

    init(id: String, taskDescription: String, quote: String, timestamp: String, dueDate: Date?) {
        self.id = id
        self.taskDescription = taskDescription
        self.quote = quote
        self.timestamp = timestamp
        self.dueDate = dueDate
    }
}
