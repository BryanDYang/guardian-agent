import SwiftUI
import SwiftData

// ChatView.tsx
struct ChatView: View {
    @Environment(\.modelContext) private var context
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

    @State private var isRefreshing = false
    @State private var projectsError: String?
    @State private var meetingsError: String?

    private var scopeError: String? { projectsError ?? meetingsError }

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
            .filter { isServerID($0.id) && $0.processingStatus == "completed" }
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
                        scopeStatus
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
            .task {
                await refreshProjects()
            }
            .task(id: selectedProjectID) {
                await refreshMeetings()
            }
            .onChange(of: projects.map(\.id)) {
                if selectedProject == nil {
                    selectedProjectID = projects.first?.id ?? ""
                    selectedMeetingID = nil
                    newChat()
                }
            }
            .refreshable {
                await refreshProjects()
                await refreshMeetings()
            }
        }
    }

    /// Changing the project or meeting starts a new chat: a conversation keeps
    /// the scope it was created with.
    private var scopeMenu: some View {
        Menu {
            Section("Projects") {
                ForEach(allProjects) { project in
                    Button {
                        guard isServerID(project.id) else { return }
                        selectedProjectID = project.id
                        selectedMeetingID = nil
                        newChat()
                    } label: {
                        if selectedProjectID == project.id {
                            Label(project.title, systemImage: "checkmark")
                        } else {
                            Text(isServerID(project.id)
                                 ? project.title : "\(project.title) (local sample)")
                        }
                    }
                    .disabled(!isServerID(project.id))
                }
            }
            Section("Meetings") {
                Button {
                    selectedMeetingID = nil
                    newChat()
                } label: {
                    if selectedMeetingID == nil {
                        Label("All", systemImage: "checkmark")
                    } else {
                        Text("All")
                    }
                }
                .disabled(selectedProject == nil)
                ForEach((selectedProject?.meetings ?? []).filter { isServerID($0.id) }
                    .sorted { $0.date > $1.date }) { meeting in
                    Button {
                        guard meeting.processingStatus == "completed" else { return }
                        selectedMeetingID = meeting.id
                        newChat()
                    } label: {
                        if selectedMeetingID == meeting.id {
                            Label(meeting.title, systemImage: "checkmark")
                        } else {
                            Text(meeting.processingStatus == "completed"
                                 ? meeting.title : "\(meeting.title) (not ready)")
                        }
                    }
                    .disabled(meeting.processingStatus != "completed")
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
        !isSending && !isRefreshing && selectedProject != nil
            && !searchableMeetings.isEmpty
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

    @ViewBuilder
    private var scopeStatus: some View {
        if let scopeError {
            Button("\(scopeError) Tap to retry.") {
                Task {
                    await refreshProjects()
                    await refreshMeetings()
                }
            }
            .font(.footnote)
            .foregroundStyle(.red)
        } else if isRefreshing {
            ProgressView("Loading meetings...")
        } else if selectedProject == nil {
            Text("Create a project in Meetings to start a chat.")
                .font(.footnote)
                .foregroundStyle(.secondary)
        } else if searchableMeetings.isEmpty {
            Text("No completed meetings in this project. Upload a recording in Meetings and wait for processing to finish.")
                .font(.footnote)
                .foregroundStyle(.secondary)
        } else {
            Text("Searches completed meetings in \(selectedProject?.title ?? "this project").")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    private func refreshProjects() async {
        do {
            try await ProjectSync.refreshProjects(context: context, api: api)
            if selectedProject == nil {
                let loaded = try context.fetch(FetchDescriptor<Project>())
                    .filter { isServerID($0.id) }.sorted { $0.createdAt < $1.createdAt }
                selectedProjectID = loaded.first?.id ?? ""
            }
            projectsError = nil
        } catch is CancellationError {
            return
        } catch {
            guard !Task.isCancelled else { return }
            projectsError = "Could not refresh projects."
        }
    }

    private func refreshMeetings() async {
        guard let project = try? context.fetch(FetchDescriptor<Project>())
            .first(where: { $0.id == selectedProjectID }) else { return }
        let projectID = project.id
        isRefreshing = true
        defer {
            if selectedProjectID == projectID { isRefreshing = false }
        }
        do {
            try await ProjectSync.refreshMeetings(project: project, context: context, api: api)
            meetingsError = nil
            if let selectedMeetingID,
               !project.meetings.contains(where: {
                   $0.id == selectedMeetingID && $0.processingStatus == "completed"
               }) {
                self.selectedMeetingID = nil
                newChat()
            }
        } catch is CancellationError {
            return
        } catch {
            guard !Task.isCancelled else { return }
            meetingsError = "Could not refresh meetings."
        }
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