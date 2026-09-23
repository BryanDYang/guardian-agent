import Foundation
import SwiftData

/// An in-memory container seeded with the mock data, for #Preview and tests.
/// Nothing here touches the on-disk store.
@MainActor
enum PreviewContainer {
    static let shared: ModelContainer = {
        do {
            let container = try ModelContainer(
                for: Project.self, Meeting.self, Attendee.self, TaskItem.self, CandidateTask.self,
                configurations: ModelConfiguration(isStoredInMemoryOnly: true)
            )
            SeedData.seed(container.mainContext)
            return container
        } catch {
            fatalError("Failed to create the preview container: \(error)")
        }
    }()
}
