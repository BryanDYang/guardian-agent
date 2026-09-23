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
