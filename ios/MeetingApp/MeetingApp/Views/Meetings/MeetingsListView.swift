import SwiftUI
import SwiftData

// MeetingsListView.tsx → the projects list (projectID == nil) and the session stream (projectID set).
struct MeetingsListView: View {
    let projectID: String?

    @Query(sort: \Project.createdAt) private var projects: [Project]
    @Query(sort: \Meeting.date, order: .reverse) private var meetings: [Meeting]

    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss

    @State private var isSelecting = false
    @State private var selectedIDs: Set<String> = []
    @State private var pendingDeletion: [Project] = []
    @State private var showDeleteConfirmation = false
    @State private var isDeleting = false
    @State private var errorMessage: String?
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
            ToolbarItem(placement: .topBarLeading) {
                if projectID == nil && !projects.isEmpty {
                    Button(isSelecting ? "Done" : "Select") {
                        isSelecting.toggle()
                        selectedIDs.removeAll()
                    }
                    .disabled(isDeleting)
                }
            }
            ToolbarItem(placement: .topBarTrailing) {
                if isSelecting {
                    Button(role: .destructive) {
                        pendingDeletion = projects.filter { selectedIDs.contains($0.id) }
                        showDeleteConfirmation = true
                    } label: {
                        if isDeleting { ProgressView() }
                        else { Image(systemName: "trash") }
                    }
                    .accessibilityLabel("Delete selected projects")
                    .disabled(selectedIDs.isEmpty || isDeleting)
                } else if let project {
                    Menu {
                        Button("Delete Project", systemImage: "trash", role: .destructive) {
                            pendingDeletion = [project]
                            showDeleteConfirmation = true
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                    .accessibilityLabel("Project actions")
                    .disabled(isDeleting)
                }
            }
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    if project == nil { showAddProject = true } else { showAddMeeting = true }
                } label: {
                    Image(systemName: "plus")
                }
                .disabled(isSelecting || isDeleting)
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
        .confirmationDialog(
            pendingDeletion.count == 1 ? "Delete this project?" : "Delete these projects?",
            isPresented: $showDeleteConfirmation, titleVisibility: .visible
        ) {
            Button(pendingDeletion.count == 1 ? "Delete Project" : "Delete \(pendingDeletion.count) Projects",
                   role: .destructive) {
                Task { await deleteProjects() }
            }
        } message: {
            Text("Projects and their meetings, tasks, and chats will be permanently deleted.")
        }
        .alert("Couldn’t delete projects", isPresented: Binding(
            get: { errorMessage != nil },
            set: { if !$0 { errorMessage = nil } }
        )) {
            Button("OK", role: .cancel) { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
        .task(id: projectID) {
            if projectID == nil { await refreshProjects() }
            await refreshMeetings()
        }
    }

    private var project: Project? {
        guard let projectID else { return nil }
        return projects.first { $0.id == projectID }
    }

    private func refreshMeetings() async {
        guard let project else { return }
        do {
            try await ProjectSync.refreshMeetings(
                project: project, context: context, api: .shared
            )
        } catch {
            // Keep the on-device list when the backend cannot be reached.
        }
    }

    private func refreshProjects() async {
        do {
            try await ProjectSync.refreshProjects(context: context, api: .shared)
        } catch {
            print("Project refresh failed: \(error)")
        }
    }

    // MARK: Projects list

    private var projectsList: some View {
        LazyVStack(spacing: 12) {
            if projects.isEmpty {
                ContentUnavailableView(
                    "No projects yet", systemImage: "folder",
                    description: Text("Tap + to create a workspace for your meetings.")
                )
                .padding(.top, 40)
            }
            ForEach(projects) { project in
                if isSelecting {
                    Button {
                        if selectedIDs.contains(project.id) { selectedIDs.remove(project.id) }
                        else { selectedIDs.insert(project.id) }
                    } label: {
                        HStack(spacing: 12) {
                            Image(systemName: selectedIDs.contains(project.id)
                                  ? "checkmark.circle.fill" : "circle")
                                .font(.title2)
                                .foregroundStyle(selectedIDs.contains(project.id) ? Color.accentColor : .secondary)
                            projectRow(project)
                        }
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(project.title)
                    .accessibilityAddTraits(selectedIDs.contains(project.id) ? .isSelected : [])
                    .disabled(isDeleting)
                } else {
                    NavigationLink(value: MeetingsRoute.project(project.id)) {
                        projectRow(project)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(16)
    }

    @MainActor
    private func deleteProjects() async {
        isDeleting = true
        defer { isDeleting = false }
        var failures: [String] = []
        for project in pendingDeletion {
            let id = project.id
            let title = project.title
            do {
                try await ProjectSync.deleteProject(project, context: context, api: .shared)
                selectedIDs.remove(id)
                if projectID == id { dismiss() }
            } catch {
                failures.append("\(title): \(error.localizedDescription)")
            }
        }
        pendingDeletion = []
        if failures.isEmpty {
            isSelecting = false
        } else {
            errorMessage = failures.joined(separator: "\n")
        }
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

            VStack(alignment: .leading, spacing: 4) {
                Text(project.title)
                    .font(.body.bold())
                    .foregroundStyle(.primary)
                if !isServerID(project.id) {
                    Text("Sample project · unavailable in Chat")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer(minLength: 0)

            if !isSelecting {
                Image(systemName: "chevron.right")
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(.tertiary)
            }
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
