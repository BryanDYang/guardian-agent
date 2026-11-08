import SwiftUI
import SwiftData

enum CompletedTaskCollection: String, Identifiable {
    case archived, deleted
    var id: String { rawValue }
    var title: String { self == .archived ? "Archived Tasks" : "Recently Deleted" }
}

struct CompletedTaskCollectionView: View {
    let collection: CompletedTaskCollection
    let projectID: String?
    let busyTaskID: String?
    let error: String?
    let refresh: @MainActor () async -> Void
    let change: @MainActor (TaskItem, String) async -> Void
    @Environment(\.dismiss) private var dismiss
    @Query(sort: \TaskItem.title) private var allTasks: [TaskItem]

    private var tasks: [TaskItem] {
        allTasks.filter { task in
            guard task.sourceMeeting?.deletedAt == nil, projectID == nil || task.project?.id == projectID else { return false }
            if collection == .archived {
                return task.archivedAt != nil && task.deletedAt == nil
            }
            guard let date = task.deletedAt else { return false }
            return date.addingTimeInterval(30 * 86400) > .now
        }
    }

    var body: some View {
        NavigationStack {
            List {
                Text(collection == .deleted
                     ? "Deleted tasks can be restored for 30 days. Changes apply to everyone in the project."
                     : "Archived tasks stay completed. Changes apply to everyone in the project.")
                    .font(.footnote).foregroundStyle(.secondary)
                if let error { Text(error).foregroundStyle(.red) }
                if tasks.isEmpty {
                    ContentUnavailableView("No tasks here", systemImage: collection == .deleted ? "trash" : "archivebox")
                }
                ForEach(tasks) { task in
                    VStack(alignment: .leading, spacing: 6) {
                        Text(task.title).font(.headline)
                        Text(task.project?.title ?? "").font(.subheadline).foregroundStyle(.secondary)
                        if let date = task.deletedAt, collection == .deleted {
                            let days = max(0, Int(ceil(date.addingTimeInterval(30 * 86400).timeIntervalSinceNow / 86400)))
                            Text("\(days) days remaining").font(.caption).foregroundStyle(.secondary)
                        }
                        HStack {
                            Button("Restore", systemImage: "arrow.uturn.backward") {
                                Task { await change(task, collection == .deleted ? "restore" : "unarchive") }
                            }
                            if collection == .archived {
                                Spacer()
                                Button("Delete", systemImage: "trash", role: .destructive) {
                                    Task { await change(task, "delete") }
                                }
                            }
                        }
                        .buttonStyle(.borderless)
                    }
                    .padding(.vertical, 4)
                    .disabled(busyTaskID != nil)
                }
            }
            .navigationTitle(collection.title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }.disabled(busyTaskID != nil)
                }
            }
            .task { await refresh() }
            .refreshable { await refresh() }
        }
    }
}
