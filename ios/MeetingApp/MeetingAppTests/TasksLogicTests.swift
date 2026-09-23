import XCTest
import SwiftData
@testable import MeetingApp

@MainActor
final class TasksLogicTests: XCTestCase {

    private let calendar = Calendar(identifier: .gregorian)

    private func date(_ year: Int, _ month: Int, _ day: Int) throws -> Date {
        try XCTUnwrap(calendar.date(from: DateComponents(year: year, month: month, day: day)))
    }

    private func seededContext() throws -> ModelContext {
        let container = try ModelContainer(
            for: Project.self, Meeting.self, Attendee.self, TaskItem.self, CandidateTask.self,
            configurations: ModelConfiguration(isStoredInMemoryOnly: true)
        )
        SeedData.seed(container.mainContext)
        return container.mainContext
    }

    private func tasks(in context: ModelContext) throws -> [TaskItem] {
        try context.fetch(FetchDescriptor<TaskItem>(sortBy: [SortDescriptor(\.id)]))
    }

    // MARK: MonthGrid

    /// September 2026 has 30 days and starts on a Tuesday, so two blank cells lead.
    func testSeptember2026Layout() throws {
        let grid = MonthGrid(month: try date(2026, 9, 12), calendar: calendar)

        XCTAssertEqual(grid.dayCount, 30)
        XCTAssertEqual(grid.leadingBlanks, 2)
        XCTAssertEqual(grid.cells.count, 42)
        XCTAssertNil(grid.cells[0])
        XCTAssertNil(grid.cells[1])
        XCTAssertEqual(calendar.component(.day, from: try XCTUnwrap(grid.cells[2])), 1)
        XCTAssertEqual(calendar.component(.day, from: try XCTUnwrap(grid.cells[31])), 30)
        XCTAssertNil(grid.cells[32])
    }

    func testLeapFebruaryHas29Days() throws {
        let grid = MonthGrid(month: try date(2024, 2, 5), calendar: calendar)
        XCTAssertEqual(grid.dayCount, 29)
    }

    /// The TS version stayed in the same year; this rolls over.
    func testSteppingBackFromJanuaryRollsTheYear() throws {
        let grid = MonthGrid(month: try date(2026, 1, 15), calendar: calendar)
        let previous = grid.shifted(by: -1)

        XCTAssertEqual(calendar.component(.year, from: previous), 2025)
        XCTAssertEqual(calendar.component(.month, from: previous), 12)
    }

    func testSteppingForwardFromDecemberRollsTheYear() throws {
        let grid = MonthGrid(month: try date(2026, 12, 3), calendar: calendar)
        let next = grid.shifted(by: 1)

        XCTAssertEqual(calendar.component(.year, from: next), 2027)
        XCTAssertEqual(calendar.component(.month, from: next), 1)
    }

    // MARK: Filtering

    func testTasksDueOnASingleDay() throws {
        let all = try tasks(in: seededContext())

        let due = all.due(on: try date(2026, 9, 16), calendar: calendar)
        XCTAssertEqual(due.map(\.id), ["t123", "t125"])

        XCTAssertEqual(all.due(on: try date(2026, 9, 18), calendar: calendar).map(\.id), ["t124"])
        XCTAssertTrue(all.due(on: try date(2026, 9, 17), calendar: calendar).isEmpty)
    }

    func testProjectFilter() throws {
        let context = try seededContext()
        let all = try tasks(in: context)

        XCTAssertEqual(all.inProject(nil).count, 3)
        XCTAssertEqual(all.inProject("p1").map(\.id), ["t123", "t124"])
        XCTAssertEqual(all.inProject("p2").map(\.id), ["t125"])
        XCTAssertTrue(all.inProject("p3").isEmpty)
    }

    func testCompletingATaskMovesItOutOfPending() throws {
        let context = try seededContext()
        let all = try tasks(in: context)
        let day = try date(2026, 9, 16)

        XCTAssertEqual(all.due(on: day, calendar: calendar).pending.count, 2)

        let task = try XCTUnwrap(all.first { $0.id == "t123" })
        task.isCompleted = true

        let dueTasks = try tasks(in: context).due(on: day, calendar: calendar)
        XCTAssertEqual(dueTasks.pending.map(\.id), ["t125"])
        XCTAssertEqual(dueTasks.completed.map(\.id), ["t123"])
    }

    /// Completion is tracked separately, so Undo restores the original state.
    func testCompletionDoesNotOverwriteState() throws {
        let context = try seededContext()
        let task = try XCTUnwrap(try tasks(in: context).first { $0.id == "t124" })

        task.isCompleted = true
        XCTAssertEqual(task.state, .inProgress)

        task.isCompleted = false
        XCTAssertEqual(task.state, .inProgress)
    }
}
