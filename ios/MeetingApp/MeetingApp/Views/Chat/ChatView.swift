import SwiftUI
import SwiftData

// ChatView.tsx
struct ChatView: View {
    @Query(sort: \Project.createdAt) private var projects: [Project]

    @State private var messages: [ChatMessage] = [ChatView.greeting] + SeedData.mockChat
    @State private var input = ""
    @State private var showHistory = false
    @State private var selectedProjectTitle = ""

    private static let greeting = ChatMessage(
        id: "greeting",
        role: .assistant,
        content: "What would you like to understand about this project?"
    )

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(spacing: 24) {
                    ForEach(messages) { message in
                        MessageBubble(message: message)
                    }
                }
                .padding(16)
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button { showHistory = true } label: {
                        Image(systemName: "line.3.horizontal")
                    }
                }
                ToolbarItem(placement: .principal) {
                    Menu {
                        Picker("Project", selection: $selectedProjectTitle) {
                            ForEach(projects) { project in
                                Text(project.title).tag(project.title)
                            }
                        }
                    } label: {
                        HStack(spacing: 4) {
                            Text(selectedProjectTitle)
                                .font(.subheadline.weight(.semibold))
                            Image(systemName: "chevron.down")
                                .font(.caption2.weight(.semibold))
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Capsule().fill(Color(.systemGray6)))
                        .foregroundStyle(.primary)
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { messages = [Self.greeting] } label: {
                        Image(systemName: "square.and.pencil")
                    }
                }
            }
            .safeAreaInset(edge: .bottom) { inputBar }
            .sheet(isPresented: $showHistory) {
                ChatHistoryDrawer()
            }
            .onAppear {
                if selectedProjectTitle.isEmpty {
                    selectedProjectTitle = projects.first?.title ?? ""
                }
            }
        }
    }

    private var inputBar: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(.secondary)

            TextField("Ask about past decisions...", text: $input, axis: .vertical)
                .lineLimit(1...5)

            // Inert, as in the TS: there's no model behind it yet.
            Button { } label: {
                Image(systemName: "arrow.up")
                    .font(.footnote.weight(.bold))
                    .foregroundStyle(Color(.systemBackground))
                    .frame(width: 28, height: 28)
                    .background(Circle().fill(input.trimmingCharacters(in: .whitespaces).isEmpty ? Color(.systemGray3) : Color.blue))
            }
            .buttonStyle(.plain)
            .disabled(input.trimmingCharacters(in: .whitespaces).isEmpty)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Capsule().fill(Color(.systemGray6)))
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(.bar)
    }
}

#Preview {
    ChatView()
        .environment(MeetingNavigator())
        .modelContainer(PreviewContainer.shared)
}
