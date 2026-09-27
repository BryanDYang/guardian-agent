import SwiftUI
import SwiftData

// TasksView.tsx
struct TasksView: View {
    @Environment(\.modelContext) private var context
    @Query(sort: \TaskItem.id) private var allTasks: [TaskItem]
    @Query(sort: \Project.createdAt) private var projects: [Project]
    @Query private var meetings: [Meeting]

    @State private var selectedDate = Calendar.current.startOfDay(for: .now)
    @State private var displayedMonth = Date()
    /// nil = "All"
    @State private var selectedProjectID: String?
    @State private var pendingTaskID: String?
    @State private var loadError: String?
    @State private var actionError: String?

    private let calendar = Calendar.current

    var body: some View {
        VStack(spacing: 0) {
            header

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
    }

    // MARK: Header

    private var header: some View {
        HStack {
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

            Spacer()

            Button { } label: {
                Image(systemName: "bell")
            }

            Menu {
                Picker("Project", selection: $selectedProjectID) {
                    Text("All").tag(String?.none)
                    ForEach(projects) { project in
                        Text(project.title).tag(String?.some(project.id))
                    }
                }
            } label: {
                Image(systemName: "line.3.horizontal.decrease")
            }
            .padding(.leading, 16)
        }
        .foregroundStyle(.red)
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
        ScrollView {
            VStack(spacing: 12) {
                if pendingTasks.isEmpty && completedTasks.isEmpty {
                    Text("No tasks due on this date.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.top, 40)
                }

                ForEach(pendingTasks) { task in
                    TaskRow(
                        task: task,
                        onToggleComplete: { Task { await markDone(task) } },
                        onDelete: { Task { await drop(task) } }
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
                            onToggleComplete: { Task { await undo(task) } },
                            onDelete: { }
                        )
                        .disabled(pendingTaskID == task.id)
                    }
                }
            }
            .padding(16)
        }
    }

    // MARK: Filtering

    private var tasksForSelectedProject: [TaskItem] {
        allTasks.filter { $0.state != .dropped }.inProject(selectedProjectID)
    }

    private var calendarRequestID: String {
        let month = Self.isoFormatter.string(from: displayedMonth)
        return "\(selectedProjectID ?? "all")|\(month)"
    }

    private var serverProjectIDs: [String] {
        let ids = selectedProjectID.map { [$0] } ?? projects.map(\.id)
        return ids.filter(isServerID)
    }

    private var tasksOnSelectedDate: [TaskItem] {
        tasksForSelectedProject.due(on: selectedDate, calendar: calendar)
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

    private func refreshCalendar() async {
        guard !serverProjectIDs.isEmpty else {
            loadError = nil
            return
        }
        guard let interval = calendar.dateInterval(of: .month, for: displayedMonth),
              let end = calendar.date(byAdding: .day, value: -1, to: interval.end) else {
            return
        }
        do {
            var loaded: [RemoteTask] = []
            for projectID in serverProjectIDs {
                let page = try await MeetingAPIClient.shared.calendarTasks(
                    projectID: projectID,
                    start: interval.start,
                    end: end
                )
                loaded.append(contentsOf: page)
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
            loadError = "Connection lost. Tap to reconnect."
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

#Preview {
    TasksView()
        .modelContainer(PreviewContainer.shared)
}
