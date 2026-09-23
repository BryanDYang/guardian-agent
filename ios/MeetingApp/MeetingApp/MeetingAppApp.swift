import SwiftUI
import SwiftData

// main.tsx → app entry point
@main
struct MeetingAppApp: App {
    @State private var navigator = MeetingNavigator()
    private let container: ModelContainer

    init() {
        do {
            container = try ModelContainer(
                for: Project.self, Meeting.self, Attendee.self, TaskItem.self, CandidateTask.self
            )
            try SeedData.seedIfNeeded(container.mainContext)
        } catch {
            fatalError("Failed to set up the model container: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            RootTabView()
                .environment(navigator)
        }
        .modelContainer(container)
    }
}
