import Foundation
import SwiftData

// types.ts → Meeting
@Model
final class Meeting {
    @Attribute(.unique) var id: String
    var title: String
    var date: Date
    /// Kept as display text ("42m 15s"), same as the TS.
    var duration: String
    var waveformPeaks: [Double]?
    var summary: [String]
    var suggestions: [Suggestion]
    var decisions: [Decision]
    /// Codable array (not a relationship) so turn order is preserved.
    var transcript: [TranscriptTurn]
    /// Name of the audio file picked in Add Meeting. The TS UI had the picker but discarded the file.
    var audioFileName: String?
    var processingStatus: String?
    var processingError: String?

    /// Replaces `projectId`. Inverse declared on Project.meetings.
    var project: Project?

    @Relationship(inverse: \Attendee.meetings) var attendees: [Attendee] = []

    @Relationship(deleteRule: .cascade, inverse: \CandidateTask.meeting)
    var candidateTasks: [CandidateTask] = []

    // Relationships (project, attendees, candidateTasks) are set after insert, in SeedData / the sheets.
    init(
        id: String,
        title: String,
        date: Date,
        duration: String,
        waveformPeaks: [Double]? = nil,
        summary: [String],
        suggestions: [Suggestion],
        decisions: [Decision],
        transcript: [TranscriptTurn],
        audioFileName: String? = nil,
        processingStatus: String = "completed",
        processingError: String? = nil
    ) {
        self.id = id
        self.title = title
        self.date = date
        self.duration = duration
        self.waveformPeaks = waveformPeaks
        self.summary = summary
        self.suggestions = suggestions
        self.decisions = decisions
        self.transcript = transcript
        self.audioFileName = audioFileName
        self.processingStatus = processingStatus
        self.processingError = processingError
    }

    /// SwiftData doesn't preserve to-many order; sort by id so the display order is stable.
    var sortedAttendees: [Attendee] {
        attendees.sorted { $0.id < $1.id }
    }

    /// TranscriptTurn stores a speaker id; resolve it against this meeting's attendees.
    func attendee(withID id: String) -> Attendee? {
        attendees.first { $0.id == id }
    }
}

// types.ts → Suggestion
struct Suggestion: Codable, Hashable, Identifiable {
    var id: String
    var text: String
}

// types.ts → Decision
struct Decision: Codable, Hashable, Identifiable {
    var id: String
    var text: String
    var timestamp: String
}

// types.ts → TranscriptTurn
struct TranscriptTurn: Codable, Hashable, Identifiable {
    var id: String
    /// Was `speaker: Attendee`. A Codable struct can't hold a SwiftData model, so it stores the id.
    var speakerID: String
    var text: String
    var startTime: String
    var endTime: String
}
