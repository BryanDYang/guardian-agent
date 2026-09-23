import Foundation

// TasksView.tsx → the project/date/completion filters.
extension Array where Element == TaskItem {
    /// nil means "All".
    func inProject(_ projectID: String?) -> [TaskItem] {
        guard let projectID else { return self }
        return filter { $0.project?.id == projectID }
    }

    func due(on date: Date, calendar: Calendar = .current) -> [TaskItem] {
        filter { task in
            guard let dueDate = task.dueDate else { return false }
            return calendar.isDate(dueDate, inSameDayAs: date)
        }
    }

    var pending: [TaskItem] { filter { !$0.isCompleted } }

    var completed: [TaskItem] { filter(\.isCompleted) }
}
