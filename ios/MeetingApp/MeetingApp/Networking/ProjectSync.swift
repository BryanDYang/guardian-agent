import Foundation
import SwiftData

/// Shared cache refresh for the Meetings and Chat project selectors.
@MainActor
enum ProjectSync {
    static func refreshProjects(context: ModelContext, api: MeetingAPIClient) async throws {
        let remote = try await api.projects()
        try Task.checkCancellation()
        let existing = try context.fetch(FetchDescriptor<Project>())
        for item in remote {
            if let project = existing.first(where: { $0.id == item.id }) {
                project.title = item.name
            } else {
                context.insert(Project(id: item.id, title: item.name, colorHex: "#5E5CE6",
                                       iconSystemName: "folder", createdAt: .now))
            }
        }
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
