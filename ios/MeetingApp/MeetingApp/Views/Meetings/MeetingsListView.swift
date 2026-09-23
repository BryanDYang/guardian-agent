import SwiftUI
import SwiftData

// MeetingsListView.tsx → the projects list (projectID == nil) and the session stream (projectID set).
struct MeetingsListView: View {
    let projectID: String?

    @Query(sort: \Project.createdAt) private var projects: [Project]
    @Query(sort: \Meeting.date, order: .reverse) private var meetings: [Meeting]

    @State private var showAddProject = false
    @State private var showAddMeeting = false

    var body: some View {
        ScrollView {
            if let project {
                sessionStream(for: project)
            } else {
                projectsList
            }
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle(project?.title ?? "Projects")
        .navigationBarTitleDisplayMode(projectID == nil ? .large : .inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    if project == nil { showAddProject = true } else { showAddMeeting = true }
                } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .sheet(isPresented: $showAddProject) {
            AddProjectSheet()
        }
        .sheet(isPresented: $showAddMeeting) {
            if let project {
                AddMeetingSheet(project: project)
            }
        }
    }

    private var project: Project? {
        guard let projectID else { return nil }
        return projects.first { $0.id == projectID }
    }

    // MARK: Projects list

    private var projectsList: some View {
        LazyVStack(spacing: 12) {
            ForEach(projects) { project in
                NavigationLink(value: MeetingsRoute.project(project.id)) {
                    projectRow(project)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(16)
    }

    private func projectRow(_ project: Project) -> some View {
        HStack(spacing: 16) {
            Text(project.title.prefix(2).uppercased())
                .font(.title3.bold())
                .foregroundStyle(Color(hex: project.colorHex))
                .frame(width: 48, height: 48)
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .fill(Color(hex: project.colorHex).opacity(0.12))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .strokeBorder(Color(hex: project.colorHex).opacity(0.25))
                )

            Text(project.title)
                .font(.body.bold())
                .foregroundStyle(.primary)

            Spacer(minLength: 0)

            Image(systemName: "chevron.right")
                .font(.footnote.weight(.semibold))
                .foregroundStyle(.tertiary)
        }
        .padding(16)
        .background(card)
        .contentShape(Rectangle())
    }

    // MARK: Session stream

    private func sessionStream(for project: Project) -> some View {
        let projectMeetings = meetings.filter { $0.project?.id == project.id }

        return LazyVStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("SESSION STREAM")
                    .font(.caption.weight(.semibold))
                    .kerning(0.5)
                Spacer()
                Label("Date", systemImage: "line.3.horizontal.decrease")
                    .font(.caption)
            }
            .foregroundStyle(.secondary)

            if projectMeetings.isEmpty {
                emptyState
            } else {
                ForEach(projectMeetings) { meeting in
                    NavigationLink(value: MeetingsRoute.meeting(meeting.id)) {
                        meetingRow(meeting)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(16)
    }

    private func meetingRow(_ meeting: Meeting) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .firstTextBaseline) {
                Text(meeting.title)
                    .font(.body.bold())
                    .foregroundStyle(.primary)
                    .lineLimit(1)
                Spacer(minLength: 8)
                Text(meeting.date.formatted(.dateTime.month(.abbreviated).day().year()))
                    .font(.caption.monospaced())
                    .foregroundStyle(.secondary)
            }

            HStack(spacing: 12) {
                Text(meeting.duration)
                    .font(.caption.monospaced())
                    .foregroundStyle(.secondary)

                WaveformView(peaks: meeting.waveformPeaks ?? [], progressIndex: 12)
                    .frame(height: 20)
            }
            .padding(8)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color(.secondarySystemGroupedBackground))
            )
        }
        .padding(16)
        .background(card)
        .contentShape(Rectangle())
    }

    private var emptyState: some View {
        VStack(spacing: 4) {
            Text("Drop MP3 here or sync from Voice Memos")
                .font(.subheadline.weight(.medium))
            Text("to assign to this workspace.")
                .font(.caption)
        }
        .foregroundStyle(.secondary)
        .frame(maxWidth: .infinity)
        .padding(.vertical, 48)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .strokeBorder(Color(.systemGray4), style: StrokeStyle(lineWidth: 2, dash: [6]))
        )
    }

    private var card: some View {
        RoundedRectangle(cornerRadius: 16)
            .fill(Color(.systemBackground))
            .shadow(color: .black.opacity(0.03), radius: 6, y: 2)
    }
}

#Preview("Projects") {
    NavigationStack {
        MeetingsListView(projectID: nil)
    }
    .modelContainer(PreviewContainer.shared)
}

#Preview("Session stream") {
    NavigationStack {
        MeetingsListView(projectID: "p1")
    }
    .modelContainer(PreviewContainer.shared)
}
