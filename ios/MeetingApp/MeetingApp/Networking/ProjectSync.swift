import Foundation
import SwiftData

/// Shared cache refresh for the Meetings and Chat project selectors.
@MainActor
enum ProjectSync {
    static func prepareCache(context: ModelContext) throws {
        for project in try context.fetch(FetchDescriptor<Project>()) {
            if ["p1", "p2", "p3"].contains(project.id) {
                removeCachedProject(project, context: context)
            } else if isServerID(project.id) {
                project.title = displayName(project.title)
                if let color = sampleColor(project.title) { project.colorHex = color }
            }
        }
        try context.save()
    }

    static func refreshProjects(context: ModelContext, api: MeetingAPIClient) async throws {
        let remote = try await api.projects()
        try Task.checkCancellation()
        let existing = try context.fetch(FetchDescriptor<Project>())
        let remoteIDs = Set(remote.map(\.id))
        for project in existing {
            if ["p1", "p2", "p3"].contains(project.id) ||
                (isServerID(project.id) && !remoteIDs.contains(project.id)) {
                removeCachedProject(project, context: context)
            }
        }
        for item in remote {
            let name = displayName(item.name)
            if let project = existing.first(where: { $0.id == item.id }) {
                project.title = name
                project.memberCount = item.memberCount
                if let color = sampleColor(name) { project.colorHex = color }
            } else {
                let project = Project(id: item.id, title: name,
                                      colorHex: sampleColor(name) ?? "#5E5CE6",
                                      iconSystemName: "folder", createdAt: .now)
                project.memberCount = item.memberCount
                context.insert(project)
            }
        }
        try context.save()
    }

    static func displayName(_ name: String) -> String {
        name.replacingOccurrences(of: #"\s*\(demo\)\s*$"#, with: "",
                                  options: [.regularExpression, .caseInsensitive])
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    static func sampleColor(_ name: String) -> String? {
        switch displayName(name).lowercased() {
        case "ai thesis": "#5E5CE6"
        case "robotics lab": "#34C759"
        case "capstone": "#FF9500"
        default: nil
        }
    }

    static func removeCachedProject(_ project: Project, context: ModelContext) {
        for task in project.tasks { context.delete(task) }
        for meeting in project.meetings { context.delete(meeting) }
        context.delete(project)
    }

    static func deleteProject(_ project: Project, context: ModelContext,
                              api: MeetingAPIClient) async throws {
        if isServerID(project.id) { try await api.deleteProject(project.id) }
        removeCachedProject(project, context: context)
        try context.save()
    }

    static func refreshMeetings(
        project: Project, context: ModelContext, api: MeetingAPIClient
    ) async throws {
        guard isServerID(project.id) else { return }
        let remote = try await api.meetings(projectID: project.id)
        try Task.checkCancellation()
        let existing = try context.fetch(FetchDescriptor<Meeting>())
        for item in remote {
            let meeting: Meeting
            if let cached = existing.first(where: { $0.id == item.id }) {
                meeting = cached
                meeting.title = item.name
                meeting.date = meetingDate(item.meetingDate)
                meeting.processingStatus = item.status
            } else {
                meeting = Meeting(id: item.id, title: item.name,
                                  date: meetingDate(item.meetingDate), duration: "Processing",
                                  summary: [], suggestions: [], decisions: [], transcript: [],
                                  processingStatus: item.status)
                context.insert(meeting)
            }
            meeting.project = project
        }
        try context.save()
    }

    private static func meetingDate(_ value: String) -> Date {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: value) { return date }
        formatter.formatOptions = [.withInternetDateTime]
        if let date = formatter.date(from: value) { return date }
        let day = DateFormatter()
        day.calendar = Calendar(identifier: .iso8601)
        day.locale = Locale(identifier: "en_US_POSIX")
        day.timeZone = TimeZone(secondsFromGMT: 0)
        day.dateFormat = "yyyy-MM-dd"
        return day.date(from: String(value.prefix(10))) ?? .now
    }
}
