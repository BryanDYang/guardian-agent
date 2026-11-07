import Foundation
import SwiftData

// types.ts → ProjectWorkspace
@Model
final class Project {
    @Attribute(.unique) var id: String
    var title: String
    var colorHex: String
    var iconSystemName: String
    var createdAt: Date
    /// This account's on-device project order. Older caches use creation order.
    var displayOrder: Int? = nil
    /// This member's server-backed archive preference.
    var archivedAt: Date? = nil
    var membershipRole: String? = nil

    var canDelete: Bool { membershipRole == "owner" || !isServerID(id) }
    /// People who have joined, from GET /api/v1/projects. nil for sample projects.
    var memberCount: Int?

    /// Replaces `meetingIds: string[]` and `Meeting.projectId`.
    @Relationship(inverse: \Meeting.project) var meetings: [Meeting] = []

    /// Replaces the free-text `Task.project` string (fixes the 'Thesis Project' / 'AI Thesis' mismatch).
    @Relationship(inverse: \TaskItem.project) var tasks: [TaskItem] = []

    init(id: String, title: String, colorHex: String, iconSystemName: String, createdAt: Date) {
        self.id = id
        self.title = title
        self.colorHex = colorHex
        self.iconSystemName = iconSystemName
        self.createdAt = createdAt
    }
}
