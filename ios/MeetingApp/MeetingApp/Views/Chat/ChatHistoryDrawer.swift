import SwiftUI
import SwiftData

// ChatView.tsx → the slide-out chat history, as a sheet.
struct ChatHistoryDrawer: View {
    @Environment(\.dismiss) private var dismiss
    @Query(sort: \Project.createdAt) private var projects: [Project]

    @State private var activeFilter = "All"

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                filterPills

                List {
                    if !recent.isEmpty {
                        Section("Recent") {
                            ForEach(recent) { item in
                                Button(item.title) { }
                                    .foregroundStyle(.primary)
                            }
                        }
                    }
                    if !previousWeek.isEmpty {
                        Section("Previous 7 Days") {
                            ForEach(previousWeek) { item in
                                Button(item.title) { }
                                    .foregroundStyle(.primary)
                            }
                        }
                    }
                    if recent.isEmpty && previousWeek.isEmpty {
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
        }
    }

    private var filterPills: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(["All"] + projects.map(\.title), id: \.self) { title in
                    Button {
                        activeFilter = title
                    } label: {
                        Text(title)
                            .font(.subheadline.weight(.medium))
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(
                                Capsule().fill(activeFilter == title ? Color.primary : Color(.systemGray6))
                            )
                            .foregroundStyle(activeFilter == title ? Color(.systemBackground) : .secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
    }

    private var filtered: [HistoryItem] {
        Self.items.filter { activeFilter == "All" || $0.project == activeFilter }
    }

    private var recent: [HistoryItem] { filtered.filter(\.isRecent) }
    private var previousWeek: [HistoryItem] { filtered.filter { !$0.isRecent } }

    // ChatView.tsx → mockHistoryItems (hardcoded there too; chats aren't persisted)
    private static let items: [HistoryItem] = [
        HistoryItem(id: "h1", title: "Thesis research notes", project: "AI Thesis", isRecent: true),
        HistoryItem(id: "h2", title: "Literature review summary", project: "AI Thesis", isRecent: true),
        HistoryItem(id: "h3", title: "Robotics integration ideas", project: "Robotics Lab", isRecent: false),
        HistoryItem(id: "h4", title: "Hardware specs meeting", project: "Robotics Lab", isRecent: false),
        HistoryItem(id: "h5", title: "Capstone presentation prep", project: "Capstone", isRecent: true)
    ]
}

struct HistoryItem: Identifiable {
    let id: String
    let title: String
    let project: String
    let isRecent: Bool
}

#Preview {
    ChatHistoryDrawer()
        .modelContainer(PreviewContainer.shared)
}
