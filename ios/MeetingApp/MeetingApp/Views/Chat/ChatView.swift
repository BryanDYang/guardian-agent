import SwiftUI
import SwiftData

// ChatView.tsx
struct ChatView: View {
    @Query(sort: \Project.createdAt) private var allProjects: [Project]

    @State private var messages: [ChatMessage] = [ChatView.greeting]
    @State private var input = ""
    @State private var showHistory = false
    @State private var selectedProjectID = ""
    /// nil searches every meeting in the project.
    @State private var selectedMeetingID: String?
    /// Created on the first question, so empty chats are never stored.
    @State private var conversationID: String?
    @State private var isSending = false
    @State private var errorMessage: String?

    private let api = MeetingAPIClient.shared

    private static let greeting = ChatMessage(
        id: "greeting",
        role: .assistant,
        content: "What would you like to understand about this project?"
    )

    /// Only server projects have searchable meetings.
    private var projects: [Project] {
        allProjects.filter { isServerID($0.id) }
    }

    private var selectedProject: Project? {
        projects.first { $0.id == selectedProjectID }
    }

    private var searchableMeetings: [Meeting] {
        (selectedProject?.meetings ?? [])
            .filter { isServerID($0.id) && ($0.processingStatus ?? "completed") == "completed" }
            .sorted { $0.date > $1.date }
    }

    private var scopeLabel: String {
        guard let project = selectedProject else { return "No project" }
        guard let meeting = searchableMeetings.first(where: { $0.id == selectedMeetingID }) else {
            return project.title
        }
        return "\(project.title) · \(meeting.title)"
    }

    var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 24) {
                        ForEach(messages) { message in
                            MessageBubble(message: message)
                                .id(message.id)
                        }
                        if isSending {
                            HStack(spacing: 8) {
                                ProgressView()
                                Text("Searching this project's meetings...")
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .id("sending")
                        }
                    }
                    .padding(16)
                }
                .onChange(of: messages.count) {
                    if let last = messages.last?.id {
                        withAnimation { proxy.scrollTo(last, anchor: .bottom) }
                    }
                }
                .onChange(of: isSending) {
                    if isSending {
                        withAnimation { proxy.scrollTo("sending", anchor: .bottom) }
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button { showHistory = true } label: {
                        Image(systemName: "line.3.horizontal")
                    }
                }
                ToolbarItem(placement: .principal) {
                    scopeMenu
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { newChat() } label: {
                        Image(systemName: "square.and.pencil")
                    }
                    .disabled(isSending)
                }
            }
            .safeAreaInset(edge: .bottom) { inputBar }
            .sheet(isPresented: $showHistory) {
                ChatHistoryDrawer { conversation in
                    showHistory = false
                    Task { await open(conversation) }
                }
            }
            .alert(
                "Chat failed",
                isPresented: Binding(
                    get: { errorMessage != nil },
                    set: { if !$0 { errorMessage = nil } }
                )
            ) {
                Button("OK", role: .cancel) { }
            } message: {
                Text(errorMessage ?? "")
            }
            .onAppear {
                if selectedProject == nil {
                    selectedProjectID = projects.first?.id ?? ""
                }
            }
        }
    }

    /// Changing the project or meeting starts a new chat: a conversation keeps
    /// the scope it was created with.
    private var scopeMenu: some View {
        Menu {
            Picker("Project", selection: Binding(
                get: { selectedProjectID },
                set: { id in
                    selectedProjectID = id
                    selectedMeetingID = nil
                    newChat()
                }
            )) {
                ForEach(projects) { project in
                    Text(project.title).tag(project.id)
                }
            }
            Picker("Search", selection: Binding(
                get: { selectedMeetingID },
                set: { id in
                    selectedMeetingID = id
                    newChat()
                }
            )) {
                Text("All meetings").tag(String?.none)
                ForEach(searchableMeetings) { meeting in
                    Text(meeting.title).tag(Optional(meeting.id))
                }
            }
        } label: {
            HStack(spacing: 4) {
                Text(scopeLabel)
                    .font(.subheadline.weight(.semibold))
                    .lineLimit(1)
                Image(systemName: "chevron.down")
                    .font(.caption2.weight(.semibold))
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(Capsule().fill(Color(.systemGray6)))
            .foregroundStyle(.primary)
        }
        .disabled(isSending)
    }

    private var canSend: Bool {
        !isSending && selectedProject != nil
            && !input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    private var inputBar: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(.secondary)

            TextField("Ask about past decisions...", text: $input, axis: .vertical)
                .lineLimit(1...5)

            Button { Task { await send() } } label: {
                Image(systemName: "arrow.up")
                    .font(.footnote.weight(.bold))
                    .foregroundStyle(Color(.systemBackground))
                    .frame(width: 28, height: 28)
                    .background(Circle().fill(canSend ? Color.blue : Color(.systemGray3)))
            }
            .buttonStyle(.plain)
            .disabled(!canSend)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Capsule().fill(Color(.systemGray6)))
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
        .background(.bar)
    }

    private func newChat() {
        conversationID = nil
        messages = [Self.greeting]
    }

    private func send() async {
        let question = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !question.isEmpty, !isSending, !selectedProjectID.isEmpty else { return }
        let pendingID = "pending-\(UUID().uuidString)"
        messages.append(ChatMessage(id: pendingID, role: .user, content: question))
        input = ""
        isSending = true
        defer { isSending = false }
        do {
            let id: String
            if let conversationID {
                id = conversationID
            } else {
                id = try await api.createConversation(
                    projectID: selectedProjectID,
                    meetingID: selectedMeetingID
                ).id
                conversationID = id
            }
            let exchange = try await api.ask(conversationID: id, question: question)
            messages.removeAll { $0.id == pendingID }
            messages.append(ChatMessage(remote: exchange.userMessage))
            messages.append(ChatMessage(remote: exchange.assistantMessage))
        } catch {
            // Nothing was stored; give the question back so it can be retried.
            messages.removeAll { $0.id == pendingID }
            input = question
            errorMessage = error.localizedDescription
        }
    }

    private func open(_ conversation: RemoteConversation) async {
        do {
            let thread = try await api.conversation(id: conversation.id)
            selectedProjectID = thread.projectID
            selectedMeetingID = thread.meetingID
            conversationID = thread.id
            messages = [Self.greeting] + thread.messages.map(ChatMessage.init(remote:))
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    ChatView()
        .environment(MeetingNavigator())
        .modelContainer(PreviewContainer.shared)
}