import SwiftUI
import SwiftData

// ChatView.tsx → the slide-out chat history, as a sheet.
struct ChatHistoryDrawer: View {
    let onSelect: (RemoteConversation) -> Void

    @Environment(\.dismiss) private var dismiss
    @Query(sort: \Project.createdAt) private var allProjects: [Project]

    /// nil = All.
    @State private var activeProjectID: String?
    @State private var conversations: [RemoteConversation] = []
    @State private var isLoading = true
    @State private var loadError: String?

    private var projects: [Project] {
        allProjects.filter { isServerID($0.id) }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                filterPills

                List {
                    if !recent.isEmpty {
                        Section("Recent") {
                            ForEach(recent) { row($0) }
                        }
                    }
                    if !older.isEmpty {
                        Section("Older") {
                            ForEach(older) { row($0) }
                        }
                    }
                    if isLoading {
                        ProgressView()
                    } else if let loadError {
                        Text(loadError)
                            .foregroundStyle(.red)
                    } else if conversations.isEmpty {
                        Text("No chat history found.")
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("Chat History")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .task(id: activeProjectID) { await load() }
        }
    }

    private func row(_ conversation: RemoteConversation) -> some View {
        Button { onSelect(conversation) } label: {
            VStack(alignment: .leading, spacing: 2) {
                Text(conversation.title ?? "Untitled chat")
                    .lineLimit(1)
                if let meetingName = conversation.meetingName {
                    Text(meetingName)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .foregroundStyle(.primary)
    }

    private var filterPills: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                pill("All", id: nil)
                ForEach(projects) { project in
                    pill(project.title, id: project.id)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
    }

    private func pill(_ title: String, id: String?) -> some View {
        Button {
            activeProjectID = id
        } label: {
            Text(title)
                .font(.subheadline.weight(.medium))
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(
                    Capsule().fill(activeProjectID == id ? Color.primary : Color(.systemGray6))
                )
                .foregroundStyle(activeProjectID == id ? Color(.systemBackground) : .secondary)
        }
        .buttonStyle(.plain)
    }

    private func load() async {
        isLoading = true
        loadError = nil
        do {
            conversations = try await MeetingAPIClient.shared.conversations(projectID: activeProjectID)
        } catch {
            conversations = []
            loadError = error.localizedDescription
        }
        isLoading = false
    }

    // The server sorts newest first; split at seven days ago.
    private var recent: [RemoteConversation] { conversations.filter(isRecent) }
    private var older: [RemoteConversation] { conversations.filter { !isRecent($0) } }

    private func isRecent(_ conversation: RemoteConversation) -> Bool {
        guard let updated = Self.timestamp.date(from: conversation.updatedAt) else { return true }
        return updated > Date.now.addingTimeInterval(-7 * 24 * 60 * 60)
    }

    /// Postgres timestamptz as FastAPI sends it, e.g. 2026-09-29T20:44:18.077475-07:00.
    private static let timestamp: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter
    }()
}

#Preview {
    ChatHistoryDrawer { _ in }
        .modelContainer(PreviewContainer.shared)
}