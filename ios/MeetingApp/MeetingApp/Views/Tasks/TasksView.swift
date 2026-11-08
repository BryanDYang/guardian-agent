import SwiftUI
import SwiftData

// TasksView.tsx
struct TasksView: View {
    @Environment(\.modelContext) private var context
    @Query(sort: \TaskItem.id) private var allTasks: [TaskItem]
    @Query(sort: \Project.createdAt) private var projects: [Project]
    @Query private var meetings: [Meeting]

    @State private var showCalendar = false
    @State private var selectedDate = Calendar.current.startOfDay(for: .now)
    @State private var displayedMonth = Date()
    /// nil = "All"
    @State private var selectedProjectID: String?
    @State private var pendingTaskID: String?
    /// One card is open at a time; opening another closes it.
    @State private var expandedTaskID: String?
    @State private var editingTask: TaskItem?
    @State private var returningTask: TaskItem?
    @State private var historyTask: TaskItem?
    @State private var completedCollection: CompletedTaskCollection?
    @State private var refreshID: UUID?
    @State private var loadError: String?
    @State private var actionError: String?

    private let calendar = Calendar.current

    var body: some View {
        VStack(spacing: 0) {
            header

            Picker("View", selection: $showCalendar) {
                Text("To-do").tag(false)
                Text("Calendar").tag(true)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, 16)
            .padding(.bottom, 12)

            if showCalendar {
            MonthCalendarView(
                month: $displayedMonth,
                selectedDate: $selectedDate,
                hasTask: hasPendingTask(on:)
            )
            .padding(.horizontal, 16)
            .padding(.bottom, 12)

            Divider()
            selectedDayBar
            Divider()
            }

            if let loadError {
                Button(loadError) { Task { await refreshCalendar() } }
                    .font(.footnote.weight(.semibold))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .padding(.horizontal, 16)
                    .background(Color.red.opacity(0.08))
                    .foregroundStyle(.red)
            }

            if let actionError {
                Text(actionError)
                    .font(.footnote)
                    .foregroundStyle(.red)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 16)
                    .padding(.top, 8)
            }

            taskList
        }
        .task(id: calendarRequestID) {
            await refreshCalendar()
        }
        .sheet(item: $completedCollection) { collection in
            CompletedTaskCollectionView(
                collection: collection, projectID: selectedProjectID,
                busyTaskID: pendingTaskID, error: actionError,
                refresh: refreshCalendar, change: changeVisibility
            )
        }
        .sheet(item: $returningTask) { task in
            ReturnTaskForReviewSheet(taskID: task.id, title: task.title, meetingName: task.sourceMeetingTitle) {
                context.delete(task)
                do { try context.save() } catch { actionError = error.localizedDescription }
            }
        }
        .sheet(item: $historyTask) { task in
            TaskChangesSheet(taskID: task.id)
        }
        .sheet(item: $editingTask) { task in
            EditTaskSheet(task: task, onSaved: applyEdit)
        }
    }

    // MARK: Header

    private var header: some View {
        HStack {
            if showCalendar {
            Menu {
                Picker("Year", selection: yearSelection) {
                    ForEach(years, id: \.self) { year in
                        Text(String(year)).tag(year)
                    }
                }
            } label: {
                HStack(spacing: 2) {
                    Image(systemName: "chevron.left")
                    Text(String(calendar.component(.year, from: displayedMonth)))
                        .font(.title3.weight(.semibold))
                }
            }

            } else {
                Text("Tasks").font(.title2.bold()).foregroundStyle(.primary)
            }

            Spacer()

            Menu {
                Picker("Project", selection: $selectedProjectID) {
                    Text("All").tag(String?.none)
                    ForEach(projects) { project in
                        Text(project.title).tag(String?.some(project.id))
                    }
                }
                Divider()
                Button("Archived Tasks", systemImage: "archivebox") {
                    completedCollection = .archived
                }
                Button("Recently Deleted", systemImage: "trash") {
                    completedCollection = .deleted
                }
            } label: {
                Image(systemName: "line.3.horizontal.decrease")
            }
            .padding(.leading, 16)
        }
        .foregroundStyle(.primary)
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
    }

    private var selectedDayBar: some View {
        HStack {
            HStack(spacing: 0) {
                if calendar.isDateInToday(selectedDate) {
                    Text("TODAY ")
                        .fontWeight(.bold)
                        .foregroundStyle(.blue)
                }

                Text(Self.isoFormatter.string(from: selectedDate))
                    .fontWeight(.medium)
                    .foregroundStyle(.blue.opacity(0.7))
            }
            .font(.footnote)

            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(Color(.systemGray6).opacity(0.5))
    }

    // MARK: Task list

    private var taskList: some View {
        List {
            Group {
                if pendingTasks.isEmpty && completedTasks.isEmpty {
                    if refreshID != nil {
                        ProgressView("Loading tasks…")
                            .frame(maxWidth: .infinity)
                            .padding(.top, 40)
                    } else {
                        Text(showCalendar ? "No tasks due on this date." : "No accepted tasks yet. Review a meeting’s suggested tasks to get started.")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .padding(.top, 40)
                    }
                }

                ForEach(pendingTasks) { task in
                    TaskRow(
                        task: task,
                        isExpanded: expandedTaskID == task.id,
                        onTap: { toggleExpanded(task) },
                        onToggleComplete: { Task { await markDone(task) } },
                        onEdit: { editingTask = task },
                        onDelete: { Task { await drop(task) } },
                        onReturnForReview: { returningTask = task },
                        onViewChanges: { historyTask = task }
                    )
                    .disabled(pendingTaskID == task.id)
                }

                if !completedTasks.isEmpty {
                    HStack {
                        Text("COMPLETED")
                            .font(.caption2.weight(.semibold))
                            .kerning(0.5)
                            .foregroundStyle(.secondary)
                        Spacer()
                    }
                    .padding(.top, 8)

                    ForEach(completedTasks) { task in
                        TaskRow(
                            task: task,
                            isExpanded: expandedTaskID == task.id,
                            onTap: { toggleExpanded(task) },
                            onToggleComplete: { Task { await undo(task) } },
                            onDelete: { }
                        )
                        .disabled(pendingTaskID == task.id)
                        .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                            Button(role: .destructive) {
                                Task { await changeVisibility(task, "delete") }
                            } label: { Label("Delete", systemImage: "trash") }
                            Button {
                                Task { await changeVisibility(task, "archive") }
                            } label: { Label("Archive", systemImage: "archivebox") }
                            .tint(.indigo)
                        }
                    }
                }
            }
            .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
            .listRowSeparator(.hidden)
            .listRowBackground(Color.clear)
        }
        .listStyle(.plain)
        .scrollContentBackground(.hidden)
    }

    // MARK: Filtering

    private var tasksForSelectedProject: [TaskItem] {
        allTasks.filter { $0.sourceMeeting?.deletedAt == nil && $0.state != .dropped && $0.archivedAt == nil && $0.deletedAt == nil }.inProject(selectedProjectID)
    }

    private var calendarRequestID: String {
        let month = Self.isoFormatter.string(from: displayedMonth)
        return "\(selectedProjectID ?? "all")|\(month)|\(showCalendar)|\(serverProjectIDs.sorted().joined(separator: ","))"
    }

    private var serverProjectIDs: [String] {
        let ids = selectedProjectID.map { [$0] } ?? projects.map(\.id)
        return ids.filter(isServerID)
    }

    private var tasksOnSelectedDate: [TaskItem] {
        showCalendar ? tasksForSelectedProject.due(on: selectedDate, calendar: calendar) : tasksForSelectedProject
    }

    private var pendingTasks: [TaskItem] { tasksOnSelectedDate.pending }

    private var completedTasks: [TaskItem] { tasksOnSelectedDate.completed }

    private func hasPendingTask(on date: Date) -> Bool {
        !tasksForSelectedProject.due(on: date, calendar: calendar).pending.isEmpty
    }

    // MARK: Year menu

    private var years: [Int] {
        let current = calendar.component(.year, from: .now)
        return Array((current - 5)...(current + 5))
    }

    private var yearSelection: Binding<Int> {
        Binding(
            get: { calendar.component(.year, from: displayedMonth) },
            set: { newYear in
                var components = calendar.dateComponents([.year, .month, .day], from: displayedMonth)
                components.year = newYear
                if let updated = calendar.date(from: components) {
                    displayedMonth = updated
                }
            }
        )
    }

    @MainActor
    private func refreshCalendar() async {
        let projectIDs = serverProjectIDs
        let scope = calendarRequestID
        let requestID = UUID()
        refreshID = requestID
        loadError = nil
        defer { if refreshID == requestID { refreshID = nil } }
        guard !projectIDs.isEmpty else { return }
        do {
            var loaded: [RemoteTask] = []
            for projectID in projectIDs {
                let page = try await MeetingAPIClient.shared.acceptedTasks(projectID: projectID)
                loaded.append(contentsOf: page)
            }
            try Task.checkCancellation()
            guard refreshID == requestID, calendarRequestID == scope else { return }
            let loadedIDs = Set(loaded.map(\.id))
            for task in allTasks where isServerID(task.id)
                && projectIDs.contains(task.project?.id ?? "")
                && !loadedIDs.contains(task.id) {
                context.delete(task)
            }
            for remote in loaded {
                try TaskSync.upsert(
                    remote,
                    projects: projects,
                    meetings: meetings,
                    context: context
                )
            }
            try context.save()
            loadError = nil
        } catch is CancellationError {
            return
        } catch {
            guard !Task.isCancelled, !MeetingAPIError.isCancellation(error),
                  refreshID == requestID, calendarRequestID == scope else { return }
            loadError = error is URLError
                ? "Couldn’t connect. Tap to retry."
                : "Couldn’t refresh tasks. Tap to retry."
        }
    }

    private func toggleExpanded(_ task: TaskItem) {
        withAnimation(.snappy(duration: 0.25)) {
            expandedTaskID = expandedTaskID == task.id ? nil : task.id
        }
    }

    private func applyEdit(_ remote: RemoteTask) {
        do {
            try TaskSync.upsert(remote, projects: projects, meetings: meetings, context: context)
            try context.save()
            actionError = nil
        } catch {
            actionError = error.localizedDescription
        }
    }

    @MainActor
    private func changeVisibility(_ task: TaskItem, _ action: String) async {
        guard isServerID(task.id) else {
            switch action {
            case "archive": task.archivedAt = .now
            case "delete": task.deletedAt = .now
            case "unarchive": task.archivedAt = nil
            default: task.deletedAt = nil
            }
            do { try context.save() } catch { actionError = error.localizedDescription }
            return
        }
        await mutate(task) {
            try await MeetingAPIClient.shared.changeTaskVisibility(id: task.id, action: action)
        }
    }

    private func markDone(_ task: TaskItem) async {
        guard isServerID(task.id) else {
            task.isCompleted = true
            return
        }
        await mutate(task) {
            try await MeetingAPIClient.shared.changeTaskState(id: task.id, state: "done")
        }
    }

    /// "Move to Trash": the task becomes dropped and leaves the list.
    private func drop(_ task: TaskItem) async {
        guard isServerID(task.id) else {
            context.delete(task)
            return
        }
        await mutate(task) {
            try await MeetingAPIClient.shared.changeTaskState(id: task.id, state: "dropped")
        }
    }

    private func undo(_ task: TaskItem) async {
        guard isServerID(task.id) else {
            task.isCompleted = false
            return
        }
        await mutate(task) {
            if let token = task.revertToken {
                return try await MeetingAPIClient.shared.revertTask(token: token)
            }
            return try await MeetingAPIClient.shared.changeTaskState(id: task.id, state: "open")
        }
    }

    private func mutate(
        _ task: TaskItem,
        _ send: () async throws -> TaskMutationResponse
    ) async {
        pendingTaskID = task.id
        defer { pendingTaskID = nil }
        do {
            let response = try await send()
            try TaskSync.upsert(
                response.task,
                revertToken: response.revertToken,
                projects: projects,
                meetings: meetings,
                context: context
            )
            try context.save()
            actionError = nil
        } catch {
            actionError = error.localizedDescription
        }
    }

    private static let isoFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()
}

/// Edits an approved task from the Tasks tab: title, assignee, and due date.
/// A deadline is optional; dated tasks also appear in the calendar.
private struct EditTaskSheet: View {
    let task: TaskItem
    let onSaved: (RemoteTask) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var title: String
    @State private var assignee: AssigneeChoice?
    @State private var dueDate: Date
    @State private var hasDueDate: Bool
    @State private var members: [RemoteMember] = []
    @State private var isSaving = false
    @State private var errorMessage: String?
    @State private var changeNote = ""

    init(task: TaskItem, onSaved: @escaping (RemoteTask) -> Void) {
        self.task = task
        self.onSaved = onSaved
        _title = State(initialValue: task.title)
        _assignee = State(
            initialValue: task.assigneeUserID.map(AssigneeChoice.member)
                ?? (task.ownerLabel.isEmpty ? nil : AssigneeChoice.speaker(task.ownerLabel))
        )
        _hasDueDate = State(initialValue: task.dueDate != nil)
        _dueDate = State(initialValue: task.dueDate ?? Calendar.current.startOfDay(for: .now))
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Task") {
                    TextField("Task", text: $title, axis: .vertical)
                        .lineLimit(2...6)
                }

                Section("Assignee") {
                    AssigneePicker(
                        selection: $assignee,
                        members: members,
                        speakers: speakers,
                        currentMemberName: task.assigneeName
                    )
                }

                Section("Change note (optional)") {
                    TextField("Why is this changing?", text: $changeNote, axis: .vertical)
                        .lineLimit(2...5)
                }
                Section("Due Date") {
                    Toggle("Has a deadline", isOn: $hasDueDate)
                    if hasDueDate { DatePicker("Date", selection: $dueDate, displayedComponents: .date) }
                }

                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Edit Task")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .disabled(isSaving)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { Task { await save() } }
                        .disabled(trimmedTitle.isEmpty || isSaving)
                }
            }
            .task { members = await AssigneePicker.loadMembers(projectID: task.project?.id) }
        }
    }

    private var trimmedTitle: String {
        title.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// Speakers from the task's meeting when it's on this device, plus the
    /// current one.
    private var speakers: [String] {
        var labels = AssigneePicker.speakers(of: task.sourceMeeting?.sortedAttendees ?? [])
        if !task.ownerLabel.isEmpty, !labels.contains(task.ownerLabel) {
            labels.insert(task.ownerLabel, at: 0)
        }
        return labels
    }

    private func save() async {
        guard isServerID(task.id) else {
            // Sample tasks only live on this device.
            task.title = trimmedTitle
            task.dueDate = hasDueDate ? dueDate : nil
            dismiss()
            return
        }
        isSaving = true
        errorMessage = nil
        defer { isSaving = false }
        do {
            let response = try await MeetingAPIClient.shared.editTask(
                id: task.id,
                title: trimmedTitle,
                dueDate: hasDueDate ? dueDate : nil,
                assignee: assignee,
                changeNote: changeNote.trimmingCharacters(in: .whitespacesAndNewlines)
            )
            onSaved(response.task)
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    TasksView()
        .modelContainer(PreviewContainer.shared)
}
