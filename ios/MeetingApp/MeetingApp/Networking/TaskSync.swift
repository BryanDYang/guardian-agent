import Foundation
import SwiftData

@MainActor
enum TaskSync {
    @discardableResult
    static func upsert(
        _ remote: RemoteTask,
        revertToken: String? = nil,
        projects: [Project],
        meetings: [Meeting],
        context: ModelContext
    ) throws -> TaskItem {
        let taskID = remote.id
        var descriptor = FetchDescriptor<TaskItem>(predicate: #Predicate { $0.id == taskID })
        let task = try context.fetch(descriptor).first ?? insert(remote, meetings: meetings, context: context)
        task.title = remote.title
        task.dueDate = remote.dueDate.flatMap(LabSyncDate.day(from:))
        task.ownerLabel = remote.ownerLabel ?? task.ownerLabel
        apply(remote.lifecycleStatus, to: task)
        if let revertToken {
            task.revertToken = revertToken
        }
        if let project = projects.first(where: { $0.id == remote.projectID }) {
            task.project = project
        }
        if let meetingID = remote.meetingID,
           let meeting = meetings.first(where: { $0.id == meetingID }) {
            task.sourceMeeting = meeting
            if task.sourceMeetingTitle.isEmpty || task.sourceMeetingTitle == "Meeting" {
                task.sourceMeetingTitle = meeting.title
            }
            if task.assignee == nil, !task.ownerLabel.isEmpty {
                task.assignee = meeting.attendees.first {
                    $0.name == task.ownerLabel || $0.id.hasSuffix(":\(task.ownerLabel)")
                }
            }
        }
        return task
    }

    private static func insert(
        _ remote: RemoteTask,
        meetings: [Meeting],
        context: ModelContext
    ) -> TaskItem {
        let meeting = meetings.first { $0.id == remote.meetingID }
        let task = TaskItem(
            id: remote.id,
            title: remote.title,
            state: .open,
            dueDate: remote.dueDate.flatMap(LabSyncDate.day(from:)),
            sourceMeetingTitle: meeting?.title ?? "Meeting",
            sourceTimestamp: ""
        )
        context.insert(task)
        return task
    }

    private static func apply(_ status: String, to task: TaskItem) {
        switch status {
        case "done":
            task.state = .done
            task.isCompleted = true
        case "dropped":
            task.state = .dropped
            task.isCompleted = false
        default:
            task.state = .open
            task.isCompleted = false
        }
    }
}
