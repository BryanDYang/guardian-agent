import XCTest
import SwiftData
@testable import MeetingApp

@MainActor
final class SeedDataTests: XCTestCase {

    private func makeContainer() throws -> ModelContainer {
        try ModelContainer(
            for: Project.self, Meeting.self, Attendee.self, TaskItem.self, CandidateTask.self,
            configurations: ModelConfiguration(isStoredInMemoryOnly: true)
        )
    }

    private func seededContext() throws -> ModelContext {
        let context = try makeContainer().mainContext
        SeedData.seed(context)
        return context
    }

    func testSeedInsertsEveryRecord() throws {
        let context = try seededContext()

        XCTAssertEqual(try context.fetchCount(FetchDescriptor<Project>()), 3)
        XCTAssertEqual(try context.fetchCount(FetchDescriptor<Meeting>()), 3)
        XCTAssertEqual(try context.fetchCount(FetchDescriptor<Attendee>()), 3)
        XCTAssertEqual(try context.fetchCount(FetchDescriptor<TaskItem>()), 3)
        XCTAssertEqual(try context.fetchCount(FetchDescriptor<CandidateTask>()), 2)
    }

    func testSeedIfNeededRunsOnlyOnce() throws {
        let context = try makeContainer().mainContext

        try SeedData.seedIfNeeded(context)
        try SeedData.seedIfNeeded(context)

        XCTAssertEqual(try context.fetchCount(FetchDescriptor<Project>()), 3)
        XCTAssertEqual(try context.fetchCount(FetchDescriptor<Meeting>()), 3)
    }

    func testMeetingRelationships() throws {
        let context = try seededContext()
        let meeting = try XCTUnwrap(fetchMeeting("m1", in: context))

        XCTAssertEqual(meeting.project?.title, "AI Thesis")
        XCTAssertEqual(meeting.attendees.count, 3)
        XCTAssertEqual(meeting.candidateTasks.count, 2)
        XCTAssertEqual(meeting.sortedAttendees.map(\.id), ["u1", "u2", "u3"])
    }

    /// The task/project mismatch from the TS ("Thesis Project" vs "AI Thesis") is resolved at seed time.
    func testTasksLinkToRealProjects() throws {
        let context = try seededContext()

        XCTAssertEqual(try fetchTask("t123", in: context)?.project?.title, "AI Thesis")
        XCTAssertEqual(try fetchTask("t125", in: context)?.project?.title, "Robotics Lab")
    }

    /// "m0" has no Meeting record, so the link is nil but the title survives.
    func testMissingSourceMeetingKeepsItsTitle() throws {
        let context = try seededContext()
        let task = try XCTUnwrap(fetchTask("t123", in: context))

        XCTAssertNil(task.sourceMeeting)
        XCTAssertEqual(task.sourceMeetingTitle, "Prev Weekly Sync")
        XCTAssertEqual(try fetchTask("t125", in: context)?.sourceMeeting?.id, "m3")
    }

    func testCandidateTaskDuplicateLink() throws {
        let context = try seededContext()
        let candidates = try context.fetch(FetchDescriptor<CandidateTask>())

        let duplicate = try XCTUnwrap(candidates.first { $0.id == "ct2" })
        XCTAssertEqual(duplicate.duplicateOf?.id, "t123")
        XCTAssertNil(candidates.first { $0.id == "ct1" }?.duplicateOf)
    }

    func testTranscriptSpeakersResolveWithinTheMeeting() throws {
        let context = try seededContext()
        let meeting = try XCTUnwrap(fetchMeeting("m1", in: context))

        XCTAssertEqual(meeting.transcript.map(\.id), ["tr1", "tr2", "tr3", "tr4"])
        for turn in meeting.transcript {
            XCTAssertNotNil(meeting.attendee(withID: turn.speakerID), "No speaker for \(turn.id)")
        }
        XCTAssertEqual(meeting.attendee(withID: "tr2")?.name, nil)
        XCTAssertEqual(meeting.attendee(withID: "u3")?.name, "Charlie Davis")
    }

    func testDueDatesLandOnTheRightDay() throws {
        let context = try seededContext()
        let task = try XCTUnwrap(fetchTask("t123", in: context))
        let components = Calendar.current.dateComponents([.year, .month, .day], from: try XCTUnwrap(task.dueDate))

        XCTAssertEqual(components.year, 2026)
        XCTAssertEqual(components.month, 9)
        XCTAssertEqual(components.day, 16)
    }

    // MARK: Helpers

    private func fetchMeeting(_ id: String, in context: ModelContext) throws -> Meeting? {
        try context.fetch(FetchDescriptor<Meeting>()).first { $0.id == id }
    }

    private func fetchTask(_ id: String, in context: ModelContext) throws -> TaskItem? {
        try context.fetch(FetchDescriptor<TaskItem>()).first { $0.id == id }
    }
}
