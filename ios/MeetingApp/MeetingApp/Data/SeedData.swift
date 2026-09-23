import Foundation
import SwiftData

// data.ts → inserted once, on first launch.
enum SeedData {

    /// Inserts the mock data only if the store is empty.
    static func seedIfNeeded(_ context: ModelContext) throws {
        var descriptor = FetchDescriptor<Project>()
        descriptor.fetchLimit = 1
        guard try context.fetch(descriptor).isEmpty else { return }

        seed(context)
        try context.save()
    }

    static func seed(_ context: ModelContext) {
        // MARK: Attendees (Tailwind classes → hex)

        let alice = Attendee(id: "u1", name: "Alice Chen", initials: "AC",
                             email: "alice@example.com", colorHex: "#3B82F6")   // bg-blue-500
        let bob = Attendee(id: "u2", name: "Bob Smith", initials: "BS",
                           email: "bob@example.com", colorHex: "#22C55E")       // bg-green-500
        let charlie = Attendee(id: "u3", name: "Charlie Davis", initials: "CD",
                               email: "charlie@example.com", colorHex: "#F59E0B") // bg-amber-500

        [alice, bob, charlie].forEach(context.insert)

        // MARK: Projects

        let thesis = Project(id: "p1", title: "AI Thesis", colorHex: "#5E5CE6",
                             iconSystemName: "brain", createdAt: day(2026, 8, 1))
        let robotics = Project(id: "p2", title: "Robotics Lab", colorHex: "#34C759",
                               iconSystemName: "cpu", createdAt: day(2026, 8, 10))
        let capstone = Project(id: "p3", title: "Capstone", colorHex: "#FF9500",
                               iconSystemName: "star", createdAt: day(2026, 9, 1))

        [thesis, robotics, capstone].forEach(context.insert)

        // MARK: Meetings

        let m1 = Meeting(
            id: "m1",
            title: "Weekly Thesis Sync",
            date: day(2026, 9, 12),
            duration: "42m 15s",
            waveformPeaks: waveform(40),
            summary: [
                "Agreed to pivot the ML architecture from standard RNNs to a transformer-based approach.",
                "Data labeling timeline is pushed back by one week due to resource constraints.",
                "Next steps involve setting up the AWS infrastructure for the new pipeline."
            ],
            suggestions: [
                Suggestion(id: "s1", text: "Consider reviewing the new paper on efficient attention mechanisms before finalizing the model depth.")
            ],
            decisions: [
                Decision(id: "d1", text: "Adopt Transformer architecture for the core extraction module.", timestamp: "12:04"),
                Decision(id: "d2", text: "Delay phase 2 user testing until Q4.", timestamp: "34:12")
            ],
            transcript: [
                TranscriptTurn(id: "tr1", speakerID: "u1",
                               text: "So looking at the latest results, the RNN just isn't converging fast enough on the larger dataset.",
                               startTime: "11:45", endTime: "11:58"),
                TranscriptTurn(id: "tr2", speakerID: "u3",
                               text: "I agree. Have we considered just moving to a transformer model? It might solve the context window issue.",
                               startTime: "11:59", endTime: "12:10"),
                TranscriptTurn(id: "tr3", speakerID: "u1",
                               text: "Yeah, let's adopt the Transformer architecture for the core extraction module. I can go ahead and spin up the GPU instances by tomorrow morning.",
                               startTime: "14:20", endTime: "14:35"),
                TranscriptTurn(id: "tr4", speakerID: "u2",
                               text: "Sounds good. Also, since we are pushing the timeline, I'll update the rubric for the labeling team.",
                               startTime: "22:10", endTime: "22:20")
            ]
        )

        let m2 = Meeting(
            id: "m2",
            title: "Baseline Review",
            date: day(2026, 9, 5),
            duration: "38m 10s",
            waveformPeaks: waveform(35),
            summary: ["Reviewed baseline metrics."],
            suggestions: [],
            decisions: [Decision(id: "d3", text: "Lock in baseline metrics.", timestamp: "10:00")],
            transcript: []
        )

        let m3 = Meeting(
            id: "m3",
            title: "Hardware Procurement",
            date: day(2026, 9, 15),
            duration: "22m 05s",
            waveformPeaks: waveform(25),
            summary: ["Finalized hardware specs."],
            suggestions: [],
            decisions: [Decision(id: "d4", text: "Order 4 LiDAR sensors.", timestamp: "05:22")],
            transcript: []
        )

        [m1, m2, m3].forEach(context.insert)

        // Relationships are set after insert.
        m1.project = thesis
        m1.attendees = [alice, bob, charlie]

        m2.project = thesis
        m2.attendees = [alice, bob]

        m3.project = robotics
        m3.attendees = [charlie, bob]

        // MARK: Tasks
        // The `project` strings are resolved to real projects here:
        // "Thesis Project" → AI Thesis, "Robotics Lab" → Robotics Lab.

        let t123 = TaskItem(id: "t123", title: "Revise labeling instructions", state: .open,
                            dueDate: day(2026, 9, 16),
                            sourceMeetingTitle: "Prev Weekly Sync", sourceTimestamp: "08:15")
        let t124 = TaskItem(id: "t124", title: "Draft literature review chapter 2", state: .inProgress,
                            dueDate: day(2026, 9, 18),
                            sourceMeetingTitle: "Prev Weekly Sync", sourceTimestamp: "42:10")
        let t125 = TaskItem(id: "t125", title: "Order new sensory modules", state: .open,
                            dueDate: day(2026, 9, 16),
                            sourceMeetingTitle: "Hardware Procurement", sourceTimestamp: "10:00")

        [t123, t124, t125].forEach(context.insert)

        t123.assignee = bob
        t123.project = thesis
        // sourceMeeting stays nil: "m0" has no Meeting record.

        t124.assignee = alice
        t124.project = thesis

        t125.assignee = charlie
        t125.project = robotics
        t125.sourceMeeting = m3

        // MARK: Candidate tasks

        let ct1 = CandidateTask(id: "ct1",
                                taskDescription: "Provision AWS EC2 instances for model training",
                                quote: "I can go ahead and spin up the GPU instances by tomorrow morning.",
                                timestamp: "14:32",
                                dueDate: day(2026, 9, 17))
        let ct2 = CandidateTask(id: "ct2",
                                taskDescription: "Update data labeling guidelines",
                                quote: "I'll update the rubric for the labeling team since we shifted the timeline.",
                                timestamp: "22:15",
                                dueDate: day(2026, 9, 23))

        [ct1, ct2].forEach(context.insert)

        ct1.assignee = alice
        ct1.meeting = m1

        ct2.assignee = bob
        ct2.meeting = m1
        ct2.duplicateOf = t123
    }

    // MARK: Chat (in-memory, not persisted)

    // data.ts → mockChat
    static let mockChat: [ChatMessage] = [
        ChatMessage(id: "msg1", role: .user,
                    content: "What did we decide about the ML architecture in the last sync?"),
        ChatMessage(id: "msg2", role: .assistant,
                    content: "During the Weekly Thesis Sync on Aug 21, the team agreed to pivot the ML architecture from standard RNNs to a transformer-based approach to address context window issues.",
                    citations: [
                        Citation(id: "cit1", meetingId: "m1",
                                 meetingTitle: "Weekly Thesis Sync", timestamp: "12:04")
                    ])
    ]

    // MARK: Helpers

    /// Components are literals here, so this can't fail.
    private static func day(_ year: Int, _ month: Int, _ day: Int) -> Date {
        Calendar.current.date(from: DateComponents(year: year, month: month, day: day))!
    }

    // data.ts → generateWaveform
    private static func waveform(_ length: Int) -> [Double] {
        (0..<length).map { _ in Double.random(in: 0.1...0.9) }
    }
}
