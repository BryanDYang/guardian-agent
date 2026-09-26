import Foundation

struct MeetingAPIClient {
    static let shared: MeetingAPIClient = {
        let config = Bundle.main.url(forResource: "LabSyncConfig", withExtension: "plist")
            .flatMap { NSDictionary(contentsOf: $0) as? [String: String] } ?? [:]
        return MeetingAPIClient(
            baseURL: config["BaseURL"].flatMap(URL.init(string:))
                ?? URL(string: "http://127.0.0.1:8000")!,
            token: config["APIToken"]
        )
    }()

    let baseURL: URL
    private let token: String?
    private let session: URLSession

    init(baseURL: URL, token: String? = nil, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.token = token
        self.session = session
    }

    func upload(
        audioURL: URL,
        title: String,
        project: String,
        date: Date
    ) async throws -> RemoteMeeting {
        let boundary = UUID().uuidString
        var request = URLRequest(url: baseURL.appending(path: "api/meetings"))
        request.httpMethod = "POST"
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
        body.appendFormField(name: "project", value: project, boundary: boundary)
        body.appendFormField(
            name: "meeting_date",
            value: date.formatted(.iso8601.year().month().day()),
            boundary: boundary
        )
        body.appendFormField(name: "permission_confirmed", value: "true", boundary: boundary)
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

    func meeting(id: String) async throws -> RemoteMeeting {
        let request = URLRequest(url: baseURL.appending(path: "api/meetings/\(id)"))
        return try await send(request)
    }

    func retry(id: String) async throws -> RemoteMeeting {
        var request = URLRequest(url: baseURL.appending(path: "api/meetings/\(id)/retry"))
        request.httpMethod = "POST"
        return try await send(request)
    }

    func purgeProject(named project: String) async throws -> Int {
        var request = URLRequest(
            url: baseURL.appending(path: "api/projects/\(project)/meetings")
        )
        request.httpMethod = "DELETE"
        let response: PurgeResponse = try await send(request)
        return response.deleted
    }

    func audioURL(id: String) -> URL {
        baseURL.appending(path: "api/meetings/\(id)/audio")
    }

    private func send<T: Decodable>(_ request: URLRequest) async throws -> T {
        var request = request
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        let (data, response) = try await session.data(for: request)
        guard let response = response as? HTTPURLResponse else {
            throw MeetingAPIError.invalidResponse
        }
        guard (200..<300).contains(response.statusCode) else {
            let detail = try? JSONDecoder().decode(ErrorResponse.self, from: data).detail
            throw MeetingAPIError.server(detail ?? "Backend returned HTTP \(response.statusCode).")
        }
        return try JSONDecoder().decode(T.self, from: data)
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
    case server(String)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            "The backend returned an invalid response."
        case .server(let detail):
            detail
        }
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
