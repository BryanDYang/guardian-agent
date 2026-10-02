import SwiftData

/// The on-device copy of server data. Cleared on every sign-out so the next
/// person to log in on this phone never sees the previous account's projects.
@MainActor
enum LocalCache {
    static func clear(_ context: ModelContext) {
        do {
            try deleteAll(CandidateTask.self, in: context)
            try deleteAll(TaskItem.self, in: context)
            try deleteAll(Meeting.self, in: context)
            try deleteAll(Attendee.self, in: context)
            try deleteAll(Project.self, in: context)
            try context.save()
        } catch {
            assertionFailure("Could not clear the local cache: \(error)")
        }
    }

    private static func deleteAll<T: PersistentModel>(_: T.Type, in context: ModelContext) throws {
        for item in try context.fetch(FetchDescriptor<T>()) {
            context.delete(item)
        }
    }
}
