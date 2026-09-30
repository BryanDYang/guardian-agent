import Foundation
import SwiftData

@MainActor
enum RemoteMeetingApplier {
    static func apply(
        _ remote: RemoteMeeting,
        to meeting: Meeting,
        context: ModelContext,
        updateCandidates: Bool = true
    ) throws {
        meeting.processingStatus = remote.status
        meeting.processingError = remote.error

        guard remote.status == "completed",
              let transcript = remote.transcript,
              let extraction = remote.extraction else {
            try context.save()
            return
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

        if updateCandidates {
            replaceCommitments(extraction.commitments, on: meeting, context: context)
        }

        try context.save()
    }

    /// Fills in a meeting loaded from the database with its stored transcript turns.
    static func applyStoredTranscript(
        _ turns: [RemoteStoredTurn],
        to meeting: Meeting,
        context: ModelContext
    ) {
        guard meeting.transcript.isEmpty, !turns.isEmpty else { return }

        var attendeesBySpeaker: [String: Attendee] = [:]
        for speaker in Set(turns.map { $0.speaker ?? "UNKNOWN" }) {
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

        meeting.transcript = turns.map { turn in
            let speaker = turn.speaker ?? "UNKNOWN"
            return TranscriptTurn(
                id: turn.turnKey,
                speakerID: attendeesBySpeaker[speaker]?.id ?? speaker,
                text: turn.content,
                startTime: timestamp(turn.startTimeMilliseconds),
                endTime: timestamp(turn.endTimeMilliseconds)
            )
        }
        meeting.duration = timestamp(turns.map(\.endTimeMilliseconds).max() ?? 0)
    }

    /// Replaces a meeting's decisions with the ones stored in the database.
    static func applyStoredDecisions(_ decisions: [RemoteStoredDecision], to meeting: Meeting) {
        meeting.decisions = decisions.map { decision in
            Decision(
                id: decision.id,
                text: decision.statement,
                timestamp: timestamp(decision.timestampMilliseconds ?? 0)
            )
        }
    }

    /// Pending database tasks become the review cards. Approved and dismissed tasks do not.
    static func replacePendingTasks(
        _ tasks: [RemoteStoredTask],
        on meeting: Meeting,
        context: ModelContext
    ) throws {
        for candidate in meeting.candidateTasks {
            context.delete(candidate)
        }
        for task in tasks where task.reviewStatus == "pending" {
            let evidence = task.evidence.first
            let candidate = CandidateTask(
                id: task.id,
                taskDescription: task.title,
                quote: evidence?.quote ?? "",
                timestamp: timestamp(evidence?.timestampMilliseconds ?? 0),
                dueDate: task.dueDate.flatMap(LabSyncDate.day(from:))
            )
            context.insert(candidate)
            candidate.meeting = meeting
            candidate.assignee = attendee(named: task.ownerLabel, on: meeting)
        }
        try context.save()
    }

    private static func replaceCommitments(
        _ commitments: [RemoteCommitment],
        on meeting: Meeting,
        context: ModelContext
    ) {
        for candidate in meeting.candidateTasks {
            context.delete(candidate)
        }
        let turnsByID = Dictionary(
            uniqueKeysWithValues: meeting.transcript.map { ($0.id, $0.startTime) }
        )
        for (index, commitment) in commitments.enumerated() {
            let evidence = commitment.evidence.first
            let candidate = CandidateTask(
                id: "\(meeting.id)-commitment-\(index)",
                taskDescription: commitment.title,
                quote: evidence?.quote ?? "",
                timestamp: evidence.flatMap { turnsByID[$0.transcriptID] } ?? "00:00",
                dueDate: nil
            )
            context.insert(candidate)
            candidate.meeting = meeting
            candidate.assignee = attendee(named: commitment.owner, on: meeting)
        }
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

    private static func attendee(named owner: String?, on meeting: Meeting) -> Attendee? {
        guard let owner else { return nil }
        return meeting.attendees.first {
            $0.name == owner || $0.name == displayName(for: owner) || $0.id.hasSuffix(":\(owner)")
        }
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
