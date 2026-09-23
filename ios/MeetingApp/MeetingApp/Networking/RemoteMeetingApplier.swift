import Foundation
import SwiftData

@MainActor
enum RemoteMeetingApplier {
    static func apply(
        _ remote: RemoteMeeting,
        to meeting: Meeting,
        context: ModelContext
    ) throws {
        meeting.processingStatus = remote.status
        meeting.processingError = remote.error

        guard remote.status == "completed",
              let transcript = remote.transcript,
              let extraction = remote.extraction else {
            try context.save()
            return
        }

        for candidate in meeting.candidateTasks {
            context.delete(candidate)
        }

        var attendeesBySpeaker: [String: Attendee] = [:]
        for speaker in Set(transcript.turns.map(\.speaker)) {
            let attendee = Attendee(
                id: "\(meeting.id):\(speaker)",
                name: displayName(for: speaker),
                initials: initials(for: speaker),
                email: "",
                colorHex: "#6B7280"
            )
            context.insert(attendee)
            attendee.meetings = [meeting]
            attendeesBySpeaker[speaker] = attendee
        }
        meeting.attendees = Array(attendeesBySpeaker.values)

        let turnsByID = Dictionary(uniqueKeysWithValues: transcript.turns.map { ($0.id, $0) })
        meeting.transcript = transcript.turns.map { turn in
            TranscriptTurn(
                id: turn.id,
                speakerID: attendeesBySpeaker[turn.speaker]?.id ?? turn.speaker,
                text: turn.content,
                startTime: timestamp(turn.startTimeMilliseconds),
                endTime: timestamp(turn.endTimeMilliseconds)
            )
        }
        meeting.duration = timestamp(transcript.turns.map(\.endTimeMilliseconds).max() ?? 0)
        meeting.summary = extraction.summary.isEmpty ? [] : [extraction.summary]

        meeting.decisions = extraction.decisions.enumerated().map { index, decision in
            Decision(
                id: "\(meeting.id)-decision-\(index)",
                text: decision.statement,
                timestamp: evidenceTimestamp(decision.evidence, turnsByID: turnsByID)
            )
        }
        meeting.suggestions = extraction.suggestions.enumerated().map { index, suggestion in
            Suggestion(id: "\(meeting.id)-suggestion-\(index)", text: suggestion.statement)
        }

        for (index, commitment) in extraction.commitments.enumerated() {
            let evidence = commitment.evidence.first
            let candidate = CandidateTask(
                id: "\(meeting.id)-commitment-\(index)",
                taskDescription: commitment.title,
                quote: evidence?.quote ?? "",
                timestamp: evidenceTimestamp(commitment.evidence, turnsByID: turnsByID),
                dueDate: nil
            )
            context.insert(candidate)
            candidate.meeting = meeting
            if let owner = commitment.owner {
                candidate.assignee = attendeesBySpeaker[owner]
            }
        }

        try context.save()
    }

    private static func evidenceTimestamp(
        _ evidence: [RemoteEvidence],
        turnsByID: [String: RemoteTurn]
    ) -> String {
        guard let id = evidence.first?.transcriptID,
              let turn = turnsByID[id] else {
            return "00:00"
        }
        return timestamp(turn.startTimeMilliseconds)
    }

    private static func timestamp(_ milliseconds: Int) -> String {
        let totalSeconds = milliseconds / 1_000
        return String(format: "%02d:%02d", totalSeconds / 60, totalSeconds % 60)
    }

    private static func displayName(for speaker: String) -> String {
        speaker.uppercased() == "UNKNOWN" ? "Unknown speaker" : speaker
    }

    private static func initials(for speaker: String) -> String {
        let result = speaker
            .split(separator: " ")
            .prefix(2)
            .compactMap(\.first)
            .map(String.init)
            .joined()
            .uppercased()
        return result.isEmpty ? "?" : result
    }
}
