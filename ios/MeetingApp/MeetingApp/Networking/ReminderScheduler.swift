import EventKit
import Foundation

enum ReminderScheduler {
    /// Copies an approved task into Reminders. Failure here does not undo the approval.
    static func addReminder(title: String, dueDay: String) async {
        guard let dueDate = LabSyncDate.day(from: dueDay) else { return }
        let store = EKEventStore()
        do {
            guard try await store.requestFullAccessToReminders(),
                  let calendar = store.defaultCalendarForNewReminders() else {
                return
            }
            let reminder = EKReminder(eventStore: store)
            reminder.title = title
            reminder.calendar = calendar
            reminder.dueDateComponents = Calendar.current.dateComponents(
                [.year, .month, .day],
                from: dueDate
            )
            try store.save(reminder, commit: true)
        } catch {
            return
        }
    }
}
