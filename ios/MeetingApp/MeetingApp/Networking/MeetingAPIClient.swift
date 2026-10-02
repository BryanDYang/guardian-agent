import Foundation
import Supabase

struct MeetingAPIClient {
    static let shared = MeetingAPIClient(baseURL: LabSyncConfig.baseURL)

    private static let uploadTimeout: TimeInterval = 15 * 60
    private static let answerTimeout: TimeInterval = 100

    let baseURL: URL
    private let auth: AuthClient
    private let session: URLSession

    init(
        baseURL: URL,
        auth: AuthClient = SupabaseService.client.auth,
        session: URLSession = .shared
    ) {
        self.baseURL = baseURL
        self.auth = auth
        self.session = session
    }

    func upload(
        audioURL: URL,
        title: String,
        projectID: String,
        date: Date
    ) async throws -> RemoteMeeting {
        let boundary = UUID().uuidString
        var request = URLRequest(url: baseURL.appending(path: "api/v1/meetings/upload"))
        request.httpMethod = "POST"
        // URLSession's idle timer only resets on response bytes, and Cloudflare buffers
        // the whole body before replying, so the default 60s fails any slow upload.
        request.timeoutInterval = Self.uploadTimeout
        request.setValue(
            "multipart/form-data; boundary=\(boundary)",
            forHTTPHeaderField: "Content-Type"
        )

        let accessed = audioURL.startAccessingSecurityScopedResource()
        defer {
            if accessed {
                audioURL.stopAccessingSecurityScopedResource()
            }
        }

        let audio = try Data(contentsOf: audioURL)
        var body = Data()
        body.appendFormField(name: "title", value: title, boundary: boundary)
        body.appendFormField(name: "project_id", value: projectID, boundary: boundary)
        body.appendFormField(
            name: "meeting_date",
            value: date.formatted(.iso8601.year().month().day()),
            boundary: boundary
        )
        body.appendFormField(name: "consent_confirmed", value: "true", boundary: boundary)
        body.appendFile(
            name: "file",
            filename: audioURL.lastPathComponent,
            mimeType: Self.mimeType(for: audioURL),
            contents: audio,
            boundary: boundary
        )
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body
        return try await send(request)
    }

    func meetings(projectID: String) async throws -> [RemoteMeetingCard] {
        let request = URLRequest(
            url: baseURL.appending(path: "api/v1/projects/\(projectID)/meetings")
        )
        return try await send(request)
    }

    func meeting(id: String) async throws -> RemoteMeeting {
        let request = URLRequest(url: baseURL.appending(path: "api/meetings/\(id)"))
        return try await send(request)
    }

    func retry(id: String) async throws -> RemoteMeeting {
        var request = URLRequest(url: baseURL.appending(path: "api/meetings/\(id)/retry"))
        request.httpMethod = "POST"
        return try await send(request)
    }

    func createProject(name: String, imagePath: String? = nil) async throws -> RemoteProject {
        var request = URLRequest(url: baseURL.appending(path: "api/v1/projects"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        var payload = ["name": name]
        if let imagePath {
            payload["image_path"] = imagePath
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        return try await send(request)
    }
    func projects() async throws -> [RemoteProject] {
        try await send(URLRequest(url: baseURL.appending(path: "api/v1/projects")))
    }

    func deleteProject(_ projectID: String) async throws {
        var request = URLRequest(url: baseURL.appending(path: "api/v1/projects/\(projectID)"))
        request.httpMethod = "DELETE"
        let _: PurgeResponse = try await send(request)
    }

    func purgeProject(_ projectID: String) async throws -> Int {
        var request = URLRequest(
            url: baseURL.appending(path: "api/projects/\(projectID)/meetings")
        )
        request.httpMethod = "DELETE"
        let response: PurgeResponse = try await send(request)
        return response.deleted
    }

    func audioURL(id: String) -> URL {
        baseURL.appending(path: "api/meetings/\(id)/audio")
    }

    func storedDetail(meetingID: String) async throws -> RemoteStoredMeeting {
        let request = URLRequest(url: baseURL.appending(path: "api/v1/meetings/\(meetingID)"))
        return try await send(request)
    }

    func calendarTasks(projectID: String, start: Date, end: Date) async throws -> [RemoteTask] {
        guard var components = URLComponents(
            url: baseURL.appending(path: "api/v1/tasks"),
            resolvingAgainstBaseURL: false
        ) else {
            throw MeetingAPIError.invalidResponse
        }
        components.queryItems = [
            URLQueryItem(name: "project_id", value: projectID),
            URLQueryItem(name: "start_date", value: LabSyncDate.string(from: start)),
            URLQueryItem(name: "end_date", value: LabSyncDate.string(from: end)),
        ]
        guard let url = components.url else { throw MeetingAPIError.invalidResponse }
        return try await send(URLRequest(url: url))
    }

    func reviewTask(
        id: String,
        action: String,
        title: String? = nil,
        dueDate: Date? = nil,
        assigneeID: String? = nil
    ) async throws -> TaskMutationResponse {
        var request = URLRequest(url: baseURL.appending(path: "api/v1/tasks/\(id)/review"))
        request.httpMethod = "PATCH"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(
            ReviewBody(
                action: action,
                title: title,
                dueDate: dueDate.map(LabSyncDate.string(from:)),
                assigneeID: assigneeID
            )
        )
        return try await send(request)
    }

    func changeTaskState(id: String, state: String) async throws -> TaskMutationResponse {
        var request = URLRequest(url: baseURL.appending(path: "api/v1/tasks/\(id)/state"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(StateBody(state: state))
        return try await send(request)
    }

    func revertTask(token: String) async throws -> TaskMutationResponse {
        var request = URLRequest(url: baseURL.appending(path: "api/v1/tasks/revert/\(token)"))
        request.httpMethod = "POST"
        return try await send(request)
    }

    func createConversation(projectID: String, meetingID: String?) async throws -> RemoteConversation {
        var request = URLRequest(url: baseURL.appending(path: "api/v1/conversations"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        var payload = ["project_id": projectID]
        if let meetingID {
            payload["meeting_id"] = meetingID
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        return try await send(request)
    }

    /// nil lists every project's conversations.
    func conversations(projectID: String?) async throws -> [RemoteConversation] {
        guard var components = URLComponents(
            url: baseURL.appending(path: "api/v1/conversations"),
            resolvingAgainstBaseURL: false
        ) else {
            throw MeetingAPIError.invalidResponse
        }
        if let projectID {
            components.queryItems = [URLQueryItem(name: "project_id", value: projectID)]
        }
        guard let url = components.url else { throw MeetingAPIError.invalidResponse }
        return try await send(URLRequest(url: url))
    }

    func conversation(id: String) async throws -> RemoteConversationThread {
        try await send(URLRequest(url: baseURL.appending(path: "api/v1/conversations/\(id)")))
    }

    func ask(conversationID: String, question: String) async throws -> RemoteExchange {
        var request = URLRequest(
            url: baseURL.appending(path: "api/v1/conversations/\(conversationID)/messages")
        )
        request.httpMethod = "POST"
        request.timeoutInterval = Self.answerTimeout
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["content": question])
        return try await send(request)
    }

    func me() async throws -> RemoteMe {
        try await send(URLRequest(url: baseURL.appending(path: "api/v1/me")))
    }

    func updateMe(displayName: String, title: String) async throws -> RemoteMe {
        var request = URLRequest(url: baseURL.appending(path: "api/v1/me"))
        request.httpMethod = "PATCH"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(
            withJSONObject: ["display_name": displayName, "title": title]
        )
        return try await send(request)
    }

    /// voiceStep is "skipped", or "placeholder" until voice enrollment ships (FR-ONB-2a).
    func completeOnboarding(voiceStep: String) async throws -> RemoteMe {
        var request = URLRequest(
            url: baseURL.appending(path: "api/v1/me/onboarding/complete")
        )
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["voice_step": voiceStep])
        return try await send(request)
    }

        func invite(projectID: String, email: String) async throws -> CreatedInvitation {
        var request = URLRequest(
            url: baseURL.appending(path: "api/v1/projects/\(projectID)/invitations")
        )
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["email": email])
        return try await send(request)
    }

    func projectInvitations(projectID: String) async throws -> [RemoteInvitation] {
        try await send(URLRequest(
            url: baseURL.appending(path: "api/v1/projects/\(projectID)/invitations")
        ))
    }

    func revokeInvitation(projectID: String, id: String) async throws {
        var request = URLRequest(
            url: baseURL.appending(path: "api/v1/projects/\(projectID)/invitations/\(id)")
        )
        request.httpMethod = "DELETE"
        let _: [String: Int] = try await send(request)
    }

    /// Pending invitations for the signed-in user's email (FR-INV-8).
    func myInvitations() async throws -> [RemoteInvitation] {
        try await send(URLRequest(url: baseURL.appending(path: "api/v1/invitations")))
    }

    func acceptInvitation(id: String) async throws -> JoinedProject {
        var request = URLRequest(url: baseURL.appending(path: "api/v1/invitations/\(id)/accept"))
        request.httpMethod = "POST"
        return try await send(request)
    }

    func declineInvitation(id: String) async throws {
        var request = URLRequest(url: baseURL.appending(path: "api/v1/invitations/\(id)/decline"))
        request.httpMethod = "POST"
        let _: [String: Int] = try await send(request)
    }

    /// From an invite link.
    func acceptInvitation(token: String) async throws -> JoinedProject {
        var request = URLRequest(url: baseURL.appending(path: "api/v1/invitations/accept-token"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["token": token])
        return try await send(request)
    }

    private func send<T: Decodable>(_ request: URLRequest) async throws -> T {
        var request = request
        let token = try await accessToken()
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let (data, response) = try await session.data(for: request)
        guard let response = response as? HTTPURLResponse else {
            throw MeetingAPIError.invalidResponse
        }
        if response.statusCode == 401 {
            // Supabase already refreshed the token, so the backend turning it down
            // means the session is over (for example, the account was deleted).
            // Signing out returns the app to log in and clears the local cache.
            try? await auth.signOut(scope: .local)
            throw MeetingAPIError.sessionEnded
        }
        guard (200..<300).contains(response.statusCode) else {
            let detail = try? JSONDecoder().decode(ErrorResponse.self, from: data).detail
            throw MeetingAPIError.server(detail ?? "Backend returned HTTP \(response.statusCode).")
        }
        return try JSONDecoder().decode(T.self, from: data)
    }

    /// The signed-in user's access token. Supabase refreshes it first when it is
    /// about to expire, and signs out if the refresh token is no longer valid.
    private func accessToken() async throws -> String {
        do {
            return try await auth.session.accessToken
        } catch AuthError.sessionMissing {
            throw MeetingAPIError.server("Sign in to continue.")
        }
    }

    private static func mimeType(for url: URL) -> String {
        switch url.pathExtension.lowercased() {
        case "wav": "audio/wav"
        case "mp3": "audio/mpeg"
        case "m4a": "audio/mp4"
        case "mp4": "video/mp4"
        case "mov": "video/quicktime"
        case "flac": "audio/flac"
        case "ogg": "audio/ogg"
        case "webm": "audio/webm"
        default: "application/octet-stream"
        }
    }
}

enum MeetingAPIError: LocalizedError {
    case invalidResponse
    /// The backend returned 401 and the app has already signed out locally.
    case sessionEnded
    case server(String)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            "The backend returned an invalid response."
        case .sessionEnded:
            "Your session ended. Sign in again."
        case .server(let detail):
            detail
        }
    }
}

struct RemoteMeetingCard: Decodable {
    let id: String
    let name: String
    let meetingDate: String
    let status: String

    enum CodingKeys: String, CodingKey {
        case id, name, status
        case meetingDate = "meeting_date"
    }
}

struct RemoteProject: Decodable {
    let id: String
    let name: String
    let imagePath: String?

    enum CodingKeys: String, CodingKey {
        case id, name
        case imagePath = "image_path"
    }
}

struct RemoteMe: Decodable {
    let displayName: String?
    let title: String?
    let onboardingStep: String

    enum CodingKeys: String, CodingKey {
        case title
        case displayName = "display_name"
        case onboardingStep = "onboarding_step"
    }
}

struct RemoteInvitation: Decodable, Identifiable {
    let id: String
    let projectID: String
    let projectName: String
    let email: String
    let invitedByName: String?

    enum CodingKeys: String, CodingKey {
        case id, email
        case projectID = "project_id"
        case projectName = "project_name"
        case invitedByName = "invited_by_name"
    }
}

struct CreatedInvitation: Decodable {
    let invitation: RemoteInvitation
    let inviteURL: URL

    enum CodingKeys: String, CodingKey {
        case invitation
        case inviteURL = "invite_url"
    }
}

struct JoinedProject: Decodable {
    let projectID: String
    let projectName: String

    enum CodingKeys: String, CodingKey {
        case projectID = "project_id"
        case projectName = "project_name"
    }
}

struct RemoteMeeting: Decodable {
    let id: String
    let title: String
    let project: String
    let date: String
    let status: String
    let error: String?
    let transcript: RemoteTranscript?
    let extraction: RemoteExtraction?
}

struct RemoteTranscript: Decodable {
    let turns: [RemoteTurn]
}

struct RemoteTurn: Decodable {
    let id: String
    let speaker: String
    let startTimeMilliseconds: Int
    let endTimeMilliseconds: Int
    let content: String

    enum CodingKeys: String, CodingKey {
        case id, speaker, content
        case startTimeMilliseconds = "start_time_ms"
        case endTimeMilliseconds = "end_time_ms"
    }
}

struct RemoteExtraction: Decodable {
    let summary: String
    let decisions: [RemoteDecision]
    let commitments: [RemoteCommitment]
    let suggestions: [RemoteDecision]
}

struct RemoteDecision: Decodable {
    let statement: String
    let evidence: [RemoteEvidence]
}

struct RemoteCommitment: Decodable {
    let title: String
    let owner: String?
    let dueDateText: String?
    let evidence: [RemoteEvidence]

    enum CodingKeys: String, CodingKey {
        case title, owner, evidence
        case dueDateText = "due_date_text"
    }
}

struct RemoteEvidence: Decodable {
    let transcriptID: String
    let quote: String

    enum CodingKeys: String, CodingKey {
        case quote
        case transcriptID = "transcript_id"
    }
}

struct RemoteTask: Decodable {
    let id: String
    let projectID: String
    let meetingID: String?
    let title: String
    let ownerLabel: String?
    let dueDate: String?
    let reviewStatus: String
    let lifecycleStatus: String

    enum CodingKeys: String, CodingKey {
        case id, title
        case projectID = "project_id"
        case meetingID = "meeting_id"
        case ownerLabel = "owner_label"
        case dueDate = "due_date"
        case reviewStatus = "review_status"
        case lifecycleStatus = "lifecycle_status"
    }
}

struct TaskMutationResponse: Decodable {
    let task: RemoteTask
    let revertToken: String?
    let eventKit: EventKitPayload?

    enum CodingKeys: String, CodingKey {
        case task
        case revertToken = "revert_token"
        case eventKit = "eventkit"
    }
}

struct EventKitPayload: Decodable {
    let title: String
    let dueDate: String

    enum CodingKeys: String, CodingKey {
        case title
        case dueDate = "due_date"
    }
}

struct RemoteStoredTask: Decodable {
    let id: String
    let title: String
    let ownerLabel: String?
    let dueDate: String?
    let reviewStatus: String
    let evidence: [RemoteTaskEvidence]

    enum CodingKeys: String, CodingKey {
        case id, title, evidence
        case ownerLabel = "owner_label"
        case dueDate = "due_date"
        case reviewStatus = "review_status"
    }
}

struct RemoteTaskEvidence: Decodable {
    let quote: String
    let timestampMilliseconds: Int?

    enum CodingKeys: String, CodingKey {
        case quote
        case timestampMilliseconds = "timestamp_ms"
    }
}

struct RemoteStoredMeeting: Decodable {
    let summary: RemoteStoredSummary?
    let tasks: [RemoteStoredTask]
    let transcript: [RemoteStoredTurn]
    let decisions: [RemoteStoredDecision]
}

struct RemoteStoredDecision: Decodable {
    let id: String
    let statement: String
    let timestampMilliseconds: Int?

    enum CodingKeys: String, CodingKey {
        case id, statement
        case timestampMilliseconds = "timestamp_ms"
    }
}

struct RemoteStoredTurn: Decodable {
    let turnKey: String
    let speaker: String?
    let startTimeMilliseconds: Int
    let endTimeMilliseconds: Int
    let content: String

    enum CodingKeys: String, CodingKey {
        case speaker, content
        case turnKey = "turn_key"
        case startTimeMilliseconds = "start_time_ms"
        case endTimeMilliseconds = "end_time_ms"
    }
}

struct RemoteStoredSummary: Decodable {
    let overview: String?
}

struct RemoteConversation: Decodable, Identifiable {
    let id: String
    let projectID: String
    /// Set when the conversation searches only this meeting.
    let meetingID: String?
    let meetingName: String?
    let title: String?
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case id, title
        case projectID = "project_id"
        case meetingID = "meeting_id"
        case meetingName = "meeting_name"
        case updatedAt = "updated_at"
    }
}

struct RemoteConversationThread: Decodable {
    let id: String
    let projectID: String
    let meetingID: String?
    let messages: [RemoteChatMessage]

    enum CodingKeys: String, CodingKey {
        case id, messages
        case projectID = "project_id"
        case meetingID = "meeting_id"
    }
}

struct RemoteChatMessage: Decodable {
    let id: String
    let role: String
    let content: String
    /// Null on user messages.
    let citations: [RemoteCitation]?
}

struct RemoteCitation: Decodable {
    let number: Int
    let kind: String
    let meetingID: String
    let meetingName: String
    let turnKey: String?
    let speaker: String?
    /// Null for a summary citation.
    let startTimeMilliseconds: Int?
    let quote: String

    enum CodingKeys: String, CodingKey {
        case number, kind, speaker, quote
        case meetingID = "meeting_id"
        case meetingName = "meeting_name"
        case turnKey = "turn_key"
        case startTimeMilliseconds = "start_time_ms"
    }
}

struct RemoteExchange: Decodable {
    let userMessage: RemoteChatMessage
    let assistantMessage: RemoteChatMessage

    enum CodingKeys: String, CodingKey {
        case userMessage = "user_message"
        case assistantMessage = "assistant_message"
    }
}

private struct ReviewBody: Encodable {
    let action: String
    let title: String?
    let dueDate: String?
    let assigneeID: String?

    enum CodingKeys: String, CodingKey {
        case action, title
        case dueDate = "due_date"
        case assigneeID = "assignee_id"
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(action, forKey: .action)
        try container.encodeIfPresent(title, forKey: .title)
        // Null clears the due date. Omitting the key would leave the stored date in place.
        try container.encode(dueDate, forKey: .dueDate)
        try container.encodeIfPresent(assigneeID, forKey: .assigneeID)
    }
}

private struct StateBody: Encodable {
    let state: String
}

enum LabSyncDate {
    static func day(from value: String) -> Date? {
        let parts = value.split(separator: "-")
        guard parts.count == 3,
              let year = Int(parts[0]),
              let month = Int(parts[1]),
              let day = Int(parts[2]) else {
            return nil
        }
        return Calendar.current.date(from: DateComponents(year: year, month: month, day: day))
    }

    static func string(from date: Date) -> String {
        let parts = Calendar.current.dateComponents([.year, .month, .day], from: date)
        return String(format: "%04d-%02d-%02d", parts.year ?? 0, parts.month ?? 0, parts.day ?? 0)
    }
}

func isServerID(_ value: String) -> Bool {
    UUID(uuidString: value) != nil
}

private struct ErrorResponse: Decodable {
    let detail: String
}

private struct PurgeResponse: Decodable {
    let deleted: Int
}

private extension Data {
    mutating func appendFormField(name: String, value: String, boundary: String) {
        append("--\(boundary)\r\n".data(using: .utf8)!)
        append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
        append("\(value)\r\n".data(using: .utf8)!)
    }

    mutating func appendFile(
        name: String,
        filename: String,
        mimeType: String,
        contents: Data,
        boundary: String
    ) {
        append("--\(boundary)\r\n".data(using: .utf8)!)
        append(
            "Content-Disposition: form-data; name=\"\(name)\"; filename=\"\(filename)\"\r\n"
                .data(using: .utf8)!
        )
        append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        append(contents)
        append("\r\n".data(using: .utf8)!)
    }
}
