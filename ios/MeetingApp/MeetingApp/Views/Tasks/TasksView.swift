import SwiftUI
import SwiftData

// TasksView.tsx
struct TasksView: View {
    @Environment(\.modelContext) private var context
    @Query(sort: \TaskItem.id) private var allTasks: [TaskItem]
    @Query(sort: \Project.createdAt) private var projects: [Project]

    @State private var selectedDate = Calendar.current.startOfDay(for: .now)
    @State private var displayedMonth = Date()
    /// nil = "All"
    @State private var selectedProjectID: String?

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

            taskList
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
            (
                Text(calendar.isDateInToday(selectedDate) ? "TODAY " : "")
                    .fontWeight(.bold)
                    .foregroundColor(.blue)
                + Text(Self.isoFormatter.string(from: selectedDate))
                    .fontWeight(.medium)
                    .foregroundColor(.blue.opacity(0.7))
            )
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
                        onToggleComplete: { task.isCompleted = true },
                        onDelete: { context.delete(task) }
                    )
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
                            onToggleComplete: { task.isCompleted = false },
                            onDelete: { }
                        )
                    }
                }
            }
            .padding(16)
        }
    }

    // MARK: Filtering

    private var tasksForSelectedProject: [TaskItem] {
        allTasks.inProject(selectedProjectID)
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
