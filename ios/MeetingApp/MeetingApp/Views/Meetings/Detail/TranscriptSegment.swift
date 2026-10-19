import SwiftUI
import SwiftData

// MeetingDetailView.tsx → activeSegment === 'transcript'
struct TranscriptSegment: View {
    let meeting: Meeting
    var onReviewSpeakers: () -> Void = {}
    var onSeek: (Int) -> Void = { _ in }

    var body: some View {
        if meeting.transcript.isEmpty {
            ContentUnavailableView(
                "No transcript",
                systemImage: "text.bubble",
                description: Text("This session hasn't been transcribed yet.")
            )
            .padding(.top, 48)
        } else {
            LazyVStack(alignment: .leading, spacing: 16) {
                if isServerID(meeting.id) && !meeting.isZoomSummary {
                    Button("Review speaker names", systemImage: "person.crop.circle.badge.questionmark", action: onReviewSpeakers)
                        .font(.subheadline.weight(.medium))
                    Text("Names from introductions need confirmation. Voice setup is optional.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                ForEach(meeting.transcript) { turn in
                    turnRow(turn)
                        .id(turn.id)
                }
            }
        }
    }

    private func turnRow(_ turn: TranscriptTurn) -> some View {
        let speaker = meeting.attendee(withID: turn.speakerID)

        return HStack(alignment: .top, spacing: 8) {
            AvatarView(
                initials: speaker?.initials ?? "?",
                colorHex: speaker?.colorHex ?? "#9CA3AF",
                size: 32
            )

            VStack(alignment: .leading, spacing: 4) {
                HStack(alignment: .firstTextBaseline, spacing: 8) {
                    Text(meeting.isZoomSummary ? "Summary document" : speaker?.name ?? "Unknown speaker")
                        .font(.caption.weight(.medium))
                        .foregroundStyle(.secondary)
                    if !meeting.isZoomSummary {
                    Button { onSeek(turn.startSeconds) } label: { Text(turn.startTime) }
                        .accessibilityLabel("Play from \(turn.startTime)")
                        .font(.system(size: 10).monospaced())
                        .foregroundStyle(.blue)
                    }
                }

                Text(turn.text)
                    .font(.subheadline)
                    .padding(12)
                    .background(
                        RoundedRectangle(cornerRadius: 16)
                            .fill(Color(.systemBackground))
                            .shadow(color: .black.opacity(0.03), radius: 4, y: 1)
                    )
            }

            Spacer(minLength: 0)
        }
    }
}

extension TranscriptTurn {
    /// "mm:ss" or "h:mm:ss" → seconds.
    var startSeconds: Int {
        Self.seconds(from: startTime)
    }

    static func seconds(from timestamp: String) -> Int {
        timestamp.split(separator: ":").reduce(0) { $0 * 60 + (Int($1) ?? 0) }
    }
}

#Preview {
    TranscriptSegmentPreview()
        .modelContainer(PreviewContainer.shared)
}

private struct TranscriptSegmentPreview: View {
    @Query private var meetings: [Meeting]

    var body: some View {
        ScrollView {
            if let meeting = meetings.first(where: { $0.id == "m1" }) {
                TranscriptSegment(meeting: meeting).padding(16)
            }
        }
        .background(Color(.systemGroupedBackground))
    }
}

struct SpeakerReviewSheet: View {
    let meeting: Meeting
    let audio: MeetingAudioPlayer
    let onSeek: (Int) -> Void
    let onSaved: () -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var speakers: [RemoteSpeaker] = []
    @State private var members: [RemoteMember] = []
    @State private var names: [String: String] = [:]
    @State private var memberIDs: [String: String] = [:]
    @State private var saving: String?
    @State private var error: String?
    @State private var loading = true

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Text("Confirm names from introductions or enter a correction. Connecting an app member assigns pending commitments already owned by this speaker. If project automatic approval is enabled, eligible clear commitments can be approved and emailed. Other voices and existing assignments are unchanged.")
                        .font(.footnote).foregroundStyle(.secondary)
                    if audio.isPlaying {
                        Button("Pause audio", systemImage: "pause.circle") { audio.pause() }
                    }
                }
                if loading { ProgressView("Loading speakers") }
                if let error {
                    Section {
                        Text(error).foregroundStyle(.red)
                        Button("Retry") { Task { await load() } }
                    }
                }
                ForEach(speakers) { speaker in
                    Section(speaker.display) {
                        if speaker.confirmed {
                            Label(speaker.assignee_user_id == nil ? "Name confirmed" : "Account connected", systemImage: "checkmark.circle")
                        }
                        ForEach(Array(speaker.suggestions.enumerated()), id: \.offset) { _, suggestion in
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Suggested: \(suggestion.name)").font(.subheadline.weight(.medium))
                                Text("“\(suggestion.quote)”").font(.caption).foregroundStyle(.secondary)
                                Button("Listen to introduction", systemImage: "play.circle") {
                                    onSeek(suggestion.timestamp_ms / 1000)
                                }
                                Button("Use this name") { names[speaker.label] = suggestion.name }
                            }
                        }
                        if Set(speaker.suggestions.map(\.name)).count > 1 {
                            Text("Different names were heard for this voice. Listen before confirming.")
                                .font(.caption).foregroundStyle(.orange)
                        }
                        TextField("Participant name", text: Binding(
                            get: { names[speaker.label] ?? "" },
                            set: { names[speaker.label] = $0 }
                        ))
                        Picker("App member (optional)", selection: Binding(
                            get: { memberIDs[speaker.label] ?? "" },
                            set: { memberIDs[speaker.label] = $0 }
                        )) {
                            Text("No account connection").tag("")
                            ForEach(members) { member in
                                Text(member.displayName ?? member.email).tag(member.id)
                            }
                        }
                        Button(saving == speaker.label ? "Saving…" : "Confirm name") {
                            Task { await confirm(speaker) }
                        }
                        .disabled(saving != nil || (names[speaker.label] ?? "").trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                }
                if !loading && speakers.isEmpty && error == nil {
                    Text("No separated speakers are available yet. Wait for processing to finish.")
                }
            }
            .navigationTitle("Speaker names")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
            .task { await load() }
            .onDisappear { audio.pause() }
        }
    }

    private func load() async {
        loading = true
        defer { loading = false }
        do {
            speakers = try await MeetingAPIClient.shared.speakers(meetingID: meeting.id)
            members = await AssigneePicker.loadMembers(projectID: meeting.project?.id)
            for speaker in speakers where names[speaker.label] == nil {
                names[speaker.label] = speaker.confirmed ? speaker.display : ""
                if let memberID = speaker.assignee_user_id { memberIDs[speaker.label] = memberID }
            }
            error = nil
        } catch { self.error = error.localizedDescription }
    }

    private func confirm(_ speaker: RemoteSpeaker) async {
        saving = speaker.label
        defer { saving = nil }
        do {
            let memberID = memberIDs[speaker.label].flatMap { $0.isEmpty ? nil : $0 }
            try await MeetingAPIClient.shared.confirmSpeaker(
                meetingID: meeting.id, label: speaker.label,
                name: names[speaker.label] ?? "", memberID: memberID
            )
            onSaved()
            await load()
        } catch { self.error = error.localizedDescription }
    }
}
