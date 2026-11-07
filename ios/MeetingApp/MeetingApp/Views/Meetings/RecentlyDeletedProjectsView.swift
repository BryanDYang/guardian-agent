import SwiftUI

struct RecentlyDeletedProjectsView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var projects: [RemoteProject] = []
    @State private var loading = true
    @State private var busy = false
    @State private var error: String?
    @State private var showPermanentConfirmation = false
    @State private var pendingDeletion: RemoteProject?

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("Deleted projects stay here for 30 days. Restore brings back their meetings, tasks, and chats.")
                        .foregroundStyle(.secondary)
                }
                if loading {
                    ProgressView()
                } else if projects.isEmpty {
                    ContentUnavailableView("No recently deleted projects", systemImage: "trash")
                }
                ForEach(projects, id: \.id) { project in
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(project.name).font(.headline)
                            if let date = RemoteProject.timestamp(project.deletedAt) {
                                let days = max(0, Int(ceil(date.addingTimeInterval(30 * 86400).timeIntervalSinceNow / 86400)))
                                Text("\(days) days remaining").font(.subheadline).foregroundStyle(.secondary)
                            }
                        }
                        Spacer()
                        Menu {
                            Button("Restore Project", systemImage: "arrow.uturn.backward") {
                                Task { await restore(project) }
                            }
                            Button("Delete Permanently", systemImage: "trash", role: .destructive) {
                                pendingDeletion = project
                                showPermanentConfirmation = true
                            }
                        } label: {
                            Image(systemName: "ellipsis.circle").frame(width: 44, height: 44)
                        }
                        .accessibilityLabel("Options for \(project.name)")
                        .disabled(busy)
                    }
                }
            }
            .navigationTitle("Recently Deleted")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }.disabled(busy)
                }
            }
            .task { await refresh() }
            .refreshable { await refresh() }
            .confirmationDialog("Delete permanently?", isPresented: $showPermanentConfirmation, titleVisibility: .visible) {
                Button("Delete Permanently", role: .destructive) {
                    if let project = pendingDeletion {
                        Task { await permanentlyDelete(project) }
                    }
                }
            } message: {
                Text("This project and all its content will be removed permanently. This cannot be undone.")
            }
            .alert("Couldn’t update projects", isPresented: Binding(
                get: { error != nil }, set: { if !$0 { error = nil } }
            )) {
                Button("OK", role: .cancel) { error = nil }
            } message: {
                Text(error ?? "")
            }
        }
    }

    private func refresh() async {
        do { projects = try await MeetingAPIClient.shared.recentlyDeletedProjects() }
        catch { self.error = error.localizedDescription }
        loading = false
    }

    private func restore(_ project: RemoteProject) async {
        busy = true
        defer { busy = false }
        do {
            try await MeetingAPIClient.shared.restoreProject(project.id)
            await refresh()
        } catch { self.error = error.localizedDescription }
    }

    private func permanentlyDelete(_ project: RemoteProject) async {
        busy = true
        defer { busy = false }
        do {
            try await MeetingAPIClient.shared.permanentlyDeleteProject(project.id)
            await refresh()
        } catch { self.error = error.localizedDescription }
    }
}
