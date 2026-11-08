import SwiftUI
import SwiftData

// MeetingsListView.tsx → the projects list (projectID == nil) and the session stream (projectID set).
struct MeetingsListView: View {
    let projectID: String?

    @Query(sort: \Project.createdAt) private var projects: [Project]
    @Query(sort: \Meeting.date, order: .reverse) private var meetings: [Meeting]

    @Environment(MeetingNavigator.self) private var navigator
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss

    @State private var sessionFilter = "Active"
    @State private var pendingSessionDeletion: Meeting?
    @State private var updatingSessionID: String?
    @State private var isSelecting = false
    @State private var isReordering = false
    @State private var showingArchived = false
    @State private var showRecentlyDeleted = false
    @State private var selectedIDs: Set<String> = []
    @State private var pendingDeletion: [Project] = []
    @State private var showDeleteConfirmation = false
    @State private var isDeleting = false
    @State private var errorMessage: String?
    @State private var showAddProject = false
    @State private var showAddMeeting = false
    @State private var inviteProject: Project?
    @State private var followupProject: Project?

    var body: some View {
        Group {
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
                    Button(isSelecting || isReordering ? "Done" : "Select") {
                        if isReordering { isReordering = false }
                        else { isSelecting.toggle() }
                        selectedIDs.removeAll()
                    }
                    .disabled(isDeleting)
                }
            }
            ToolbarItem(placement: .topBarTrailing) {
                if isSelecting {
                    Button(role: .destructive) {
                        pendingDeletion = projects.filter { selectedIDs.contains($0.id) && $0.canDelete }
                        showDeleteConfirmation = true
                    } label: {
                        if isDeleting { ProgressView() }
                        else { Image(systemName: "trash") }
                    }
                    .accessibilityLabel("Delete selected projects")
                    .disabled(selectedIDs.isEmpty || isDeleting)
                } else if let project {
                    Menu {
                        if isServerID(project.id) {
                            Button("Follow-through", systemImage: "envelope") {
                                followupProject = project
                            }
                            Button("Invite People", systemImage: "person.badge.plus") {
                                inviteProject = project
                            }
                        }
                        Button(project.archivedAt == nil ? "Archive Project" : "Restore Project",
                               systemImage: project.archivedAt == nil ? "archivebox" : "arrow.uturn.backward") {
                            setArchived(project, archived: project.archivedAt == nil)
                        }
                        Button(project.canDelete ? "Delete Project" : "Leave Project",
                               systemImage: project.canDelete ? "trash" : "rectangle.portrait.and.arrow.right",
                               role: .destructive) {
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
                if projectID == nil && !isSelecting && !isReordering {
                    Menu {
                        Button("Recently Deleted", systemImage: "trash") {
                            showRecentlyDeleted = true
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                    .accessibilityLabel("Projects options")
                }
            }
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    if project == nil { showAddProject = true } else { showAddMeeting = true }
                } label: {
                    Image(systemName: "plus")
                }
                .disabled(isSelecting || isReordering || isDeleting)
            }
        }
        .sheet(isPresented: $showRecentlyDeleted, onDismiss: {
            Task { await refreshProjects() }
        }) {
            RecentlyDeletedProjectsView()
        }
        .sheet(isPresented: $showAddProject) {
            AddProjectSheet()
        }
        .sheet(isPresented: $showAddMeeting) {
            if let project {
                AddMeetingSheet(project: project)
            }
        }
        .sheet(item: $inviteProject) { project in
            InviteMembersSheet(project: project)
        }
        .sheet(item: $followupProject) { project in
            FollowupSettingsSheet(projectID: project.id)
        }
        .confirmationDialog(
            pendingDeletion.first?.canDelete == false ? "Leave this project?" : "Move to Recently Deleted?",
            isPresented: $showDeleteConfirmation, titleVisibility: .visible
        ) {
            Button(pendingDeletion.first?.canDelete == false ? "Leave Project" : "Delete Project",
                   role: .destructive) {
                Task { await deleteProjects() }
            }
        } message: {
            Text(pendingDeletion.first?.canDelete == false
                 ? "You will lose access to this project. An owner can invite you back."
                 : "You can restore this project and its content within 30 days. Follow-through emails will stop for everyone.")
        }
        .confirmationDialog("Delete this session?", isPresented: Binding(
            get: { pendingSessionDeletion != nil },
            set: { if !$0 { pendingSessionDeletion = nil } }
        ), titleVisibility: .visible) {
            Button("Delete Session", role: .destructive) {
                if let meeting = pendingSessionDeletion { updateSession(meeting, action: "delete") }
                pendingSessionDeletion = nil
            }
        } message: {
            Text("This moves the session and its content to Recently Deleted for 30 days. Its tasks will be hidden and queued emails will stop for everyone in this project.")
        }
        .alert("Couldn’t update", isPresented: Binding(
            get: { errorMessage != nil },
            set: { if !$0 { errorMessage = nil } }
        )) {
            Button("OK", role: .cancel) { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
        .task(id: projectID) {
            if projectID == nil {
                await refreshProjects()
                // Runs until the project list leaves the screen.
                await followProjectEvents()
            }
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

    /// Keeps member counts live while the project list is on screen. The server
    /// nudges on every membership change and the list re-fetches. Reconnects when
    /// the stream ends (every 10 minutes) or drops, waiting longer after each error.
    private func followProjectEvents() async {
        var delay: Duration = .seconds(1)
        while !Task.isCancelled {
            do {
                try await MeetingAPIClient.shared.followProjectEvents {
                    await refreshProjects()
                }
                delay = .seconds(1)
            } catch MeetingAPIError.sessionEnded {
                return
            } catch {
                // Offline, or the backend restarted: try again later.
                delay = min(delay * 2, .seconds(60))
            }
            try? await Task.sleep(for: delay)
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

    private var orderedProjects: [Project] {
        projects.filter { ($0.archivedAt != nil) == showingArchived }.sorted {
            if $0.displayOrder != $1.displayOrder {
                return ($0.displayOrder ?? Int.max) < ($1.displayOrder ?? Int.max)
            }
            if $0.createdAt != $1.createdAt { return $0.createdAt < $1.createdAt }
            return $0.id < $1.id
        }
    }

    private var projectsList: some View {
        List {
            Picker("Project list", selection: $showingArchived) {
                Text("Active").tag(false)
                Text("Archived").tag(true)
            }
            .pickerStyle(.segmented)
            .disabled(isSelecting || isReordering)
            .listRowSeparator(.hidden)
            .listRowBackground(Color.clear)
            if orderedProjects.isEmpty {
                ContentUnavailableView(
                    showingArchived ? "No archived projects" : "No active projects", systemImage: showingArchived ? "archivebox" : "folder",
                    description: Text(showingArchived ? "Projects you archive will appear here." : "Tap + to create a workspace for your meetings.")
                )
                .padding(.top, 40)
            }
            ForEach(orderedProjects) { project in
                Group {
                    if isSelecting {
                        Button {
                            guard project.canDelete else { return }
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
                        .disabled(isDeleting || !project.canDelete)
                    } else if isReordering {
                        projectRow(project)
                    } else {
                        HStack(spacing: 8) {
                            NavigationLink(value: MeetingsRoute.project(project.id)) {
                                projectRow(project)
                            }
                            .buttonStyle(.plain)
                            Menu {
                                if isServerID(project.id) {
                                    Button("Follow-through", systemImage: "envelope") {
                                        followupProject = project
                                    }
                                    Button("Invite People", systemImage: "person.badge.plus") {
                                        inviteProject = project
                                    }
                                }
                                Button(showingArchived ? "Restore Project" : "Archive Project",
                                       systemImage: showingArchived ? "arrow.uturn.backward" : "archivebox") {
                                    setArchived(project, archived: !showingArchived)
                                }
                                Button("Reorder Projects", systemImage: "arrow.up.arrow.down") {
                                    withAnimation { isReordering = true }
                                }
                                Button(project.canDelete ? "Delete Project" : "Leave Project",
                               systemImage: project.canDelete ? "trash" : "rectangle.portrait.and.arrow.right",
                               role: .destructive) {
                                    pendingDeletion = [project]
                                    showDeleteConfirmation = true
                                }
                            } label: {
                                Image(systemName: "ellipsis")
                                    .font(.body.weight(.semibold))
                                    .foregroundStyle(.secondary)
                                    .frame(width: 44, height: 44)
                                    .contentShape(Rectangle())
                            }
                            .menuStyle(.borderlessButton)
                            .accessibilityLabel("Options for \(project.title)")
                            .disabled(isDeleting)
                        }
                    }
                }
                .simultaneousGesture(
                    LongPressGesture(minimumDuration: 0.5).onEnded { _ in
                        guard !isSelecting && !isDeleting else { return }
                        withAnimation { isReordering = true }
                    }
                )
                .accessibilityHint(isSelecting ? "" : "Touch and hold to reorder projects")
                .accessibilityAction(named: Text("Reorder projects")) {
                    guard !isSelecting && !isDeleting else { return }
                    isReordering = true
                }
                .moveDisabled(!isReordering)
                .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                    if !isSelecting && !isReordering {
                        Button {
                            setArchived(project, archived: !showingArchived)
                        } label: {
                            Label(showingArchived ? "Restore" : "Archive",
                                  systemImage: showingArchived ? "arrow.uturn.backward" : "archivebox")
                        }
                        .tint(.indigo)
                    }
                }
                .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
                .listRowSeparator(.hidden)
                .listRowBackground(card.padding(.horizontal, 16).padding(.vertical, 6))
            }
            .onMove(perform: moveProjects)
        }
        .listStyle(.plain)
        .scrollContentBackground(.hidden)
        .environment(\.editMode, .constant(isReordering ? .active : .inactive))
    }

    private func moveProjects(from source: IndexSet, to destination: Int) {
        var reordered = orderedProjects
        let previous = reordered.map { ($0, $0.displayOrder) }
        reordered.move(fromOffsets: source, toOffset: destination)
        for (index, project) in reordered.enumerated() {
            project.displayOrder = index
        }
        do {
            try context.save()
        } catch {
            for (project, order) in previous { project.displayOrder = order }
            errorMessage = error.localizedDescription
        }
    }

    private func setArchived(_ project: Project, archived: Bool) {
        Task {
            do {
                if isServerID(project.id) {
                    try await MeetingAPIClient.shared.archiveProject(project.id, archived: archived)
                }
                project.archivedAt = archived ? Date() : nil
                try context.save()
                if archived && projectID == project.id { dismiss() }
            } catch {
                errorMessage = error.localizedDescription
                await refreshProjects()
            }
        }
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
                if !project.canDelete {
                    try await MeetingAPIClient.shared.leaveProject(id)
                    ProjectSync.removeCachedProject(project, context: context)
                    try context.save()
                } else {
                    try await ProjectSync.deleteProject(project, context: context, api: .shared)
                }
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
                } else if let count = project.memberCount {
                    Text(count == 1 ? "1 member" : "\(count) members")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer(minLength: 0)

        }
        .padding(16)
        .contentShape(Rectangle())
        .accessibilityElement(children: .combine)
    }

    // MARK: Session stream

    private func sessionStream(for project: Project) -> some View {
        let projectMeetings = meetings.filter {
            guard $0.project?.id == project.id else { return false }
            if sessionFilter == "Recently Deleted" {
                return $0.deletedAt.map { $0 > Date().addingTimeInterval(-30 * 86400) } ?? false
            }
            return $0.deletedAt == nil && ($0.archivedAt != nil) == (sessionFilter == "Archived")
        }

        return List {
            HStack {
                Text("SESSION STREAM")
                    .font(.caption.weight(.semibold))
                    .kerning(0.5)
                    .foregroundStyle(.secondary)
                Spacer()
                Menu {
                    Picker("Sessions", selection: $sessionFilter) {
                        Text("Active").tag("Active")
                        Text("Archived").tag("Archived")
                        Text("Recently Deleted").tag("Recently Deleted")
                    }
                } label: {
                    Label(sessionFilter, systemImage: "line.3.horizontal.decrease")
                        .font(.subheadline)
                }
                .accessibilityLabel("Session filter: \(sessionFilter)")
            }
            .listRowBackground(Color.clear)
            .listRowSeparator(.hidden)

            if sessionFilter != "Active" {
                Text(sessionFilter == "Recently Deleted"
                     ? "Deleted sessions can be restored for 30 days. Restoring keeps their previous archive status."
                     : "Archived sessions keep their tasks and remain available in Chat. Restore brings them back to the active stream.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .listRowBackground(Color.clear)
                    .listRowSeparator(.hidden)
            }
            if projectMeetings.isEmpty {
                ContentUnavailableView(
                    sessionFilter == "Active" ? "No sessions yet" : "No \(sessionFilter.lowercased()) sessions",
                    systemImage: sessionFilter == "Recently Deleted" ? "trash" : "waveform",
                    description: Text(sessionFilter == "Active" ? "Tap + to record or import a meeting." : "Sessions you move here will appear here.")
                )
                .listRowBackground(Color.clear)
                .listRowSeparator(.hidden)
            }
            ForEach(projectMeetings) { meeting in
                VStack(spacing: 0) {
                    if sessionFilter == "Recently Deleted" {
                        VStack(alignment: .leading, spacing: 8) {
                            meetingRow(meeting)
                            HStack {
                                if let deleted = meeting.deletedAt {
                                    let days = max(1, Int(ceil(deleted.addingTimeInterval(30 * 86400).timeIntervalSinceNow / 86400)))
                                    Text("\(days) days left")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                Button("Restore") { updateSession(meeting, action: "restore") }
                                    .buttonStyle(.borderless)
                            }
                            .padding(.horizontal, 16)
                            .padding(.bottom, 12)
                        }
                    } else {
                        HStack(spacing: 0) {
                            meetingRow(meeting)
                            Image(systemName: "chevron.right")
                                .font(.body.weight(.semibold))
                                .foregroundStyle(.tertiary)
                                .padding(.trailing, 16)
                        }
                        .contentShape(Rectangle())
                        .onTapGesture { navigator.open(meetingID: meeting.id) }
                        .accessibilityElement(children: .combine)
                        .accessibilityAddTraits(.isButton)
                        .accessibilityAction { navigator.open(meetingID: meeting.id) }
                    }
                }
                .background(card)
                .disabled(updatingSessionID != nil)
                .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                    if sessionFilter == "Recently Deleted" {
                        Button("Restore", systemImage: "arrow.uturn.backward") {
                            updateSession(meeting, action: "restore")
                        }.tint(.indigo)
                    } else {
                        Button("Delete", systemImage: "trash", role: .destructive) {
                            pendingSessionDeletion = meeting
                        }
                        Button(sessionFilter == "Archived" ? "Restore" : "Archive",
                               systemImage: sessionFilter == "Archived" ? "arrow.uturn.backward" : "archivebox") {
                            updateSession(meeting, action: sessionFilter == "Archived" ? "unarchive" : "archive")
                        }.tint(.indigo)
                    }
                }
                .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
                .listRowBackground(Color.clear)
                .listRowSeparator(.hidden)
            }
        }
        .listStyle(.plain)
        .scrollContentBackground(.hidden)
        .refreshable { await refreshMeetings() }
        .id(sessionFilter)
    }

    private func updateSession(_ meeting: Meeting, action: String) {
        guard updatingSessionID == nil else { return }
        updatingSessionID = meeting.id
        Task { @MainActor in
            defer { updatingSessionID = nil }
            do {
                if isServerID(meeting.id) {
                    try await MeetingAPIClient.shared.setSessionVisibility(meeting.id, action: action)
                }
                switch action {
                case "archive": meeting.archivedAt = .now
                case "unarchive": meeting.archivedAt = nil
                case "delete": meeting.deletedAt = .now
                default: meeting.deletedAt = nil
                }
                try context.save()
                await refreshMeetings()
            } catch { errorMessage = error.localizedDescription }
        }
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
    .environment(MeetingNavigator())
    .modelContainer(PreviewContainer.shared)
}

#Preview("Session stream") {
    NavigationStack {
        MeetingsListView(projectID: "p1")
    }
    .environment(MeetingNavigator())
    .modelContainer(PreviewContainer.shared)
}
