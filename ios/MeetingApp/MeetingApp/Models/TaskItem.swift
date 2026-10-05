import Foundation
import SwiftData

// types.ts → TaskState
enum TaskState: String, Codable, CaseIterable {
    case open = "Open"
    case inProgress = "In-Progress"
    case blocked = "Blocked"
    case done = "Done"
    case dropped = "Dropped"
}

// types.ts → Task (renamed: `Task` clashes with Swift concurrency's Task)
@Model
final class TaskItem {
    @Attribute(.unique) var id: String
    var title: String
    var state: TaskState
    /// Day-level due date (TS used "YYYY-MM-DD" strings).
    var dueDate: Date?
    /// Kept as text because some source meetings (e.g. "m0") don't exist as Meeting records.
    var sourceMeetingTitle: String
    var sourceTimestamp: String
    /// Persists TasksView's `completedTaskIds` set. Separate from `state`, as in the TS,
    /// so Undo restores the original state.
    var isCompleted: Bool = false
    /// Raw diarizer owner when the task has no linked attendee yet.
    var ownerLabel: String = ""
    /// Project member the task is assigned to, from the server. Wins over ownerLabel.
    var assigneeUserID: String?
    var assigneeName: String?
    /// First evidence quote, shown when the row is expanded in the Tasks tab.
    var sourceQuote: String = ""
    /// Latest audit token from a lifecycle change, used by Undo.
    var revertToken: String?

    // Relationships — set after insert.
    var assignee: Attendee?
    /// Replaces `sourceMeetingId`. Nil when the source meeting doesn't exist.
    var sourceMeeting: Meeting?
    /// Replaces the `project` string. Inverse declared on Project.tasks.
    var project: Project?

    init(
        id: String,
        title: String,
        state: TaskState,
        dueDate: Date?,
        sourceMeetingTitle: String,
        sourceTimestamp: String
    ) {
        self.id = id
        self.title = title
        self.state = state
        self.dueDate = dueDate
        self.sourceMeetingTitle = sourceMeetingTitle
        self.sourceTimestamp = sourceTimestamp
    }
}
