import Foundation
import SwiftData

// types.ts → Attendee
@Model
final class Attendee {
    @Attribute(.unique) var id: String
    var name: String
    var initials: String
    var email: String
    /// Was a Tailwind class ("bg-blue-500"). Stored as hex because SwiftData can't store Color.
    var colorHex: String

    /// Inverse of Meeting.attendees (declared on the Meeting side).
    var meetings: [Meeting] = []

    init(id: String, name: String, initials: String, email: String, colorHex: String) {
        self.id = id
        self.name = name
        self.initials = initials
        self.email = email
        self.colorHex = colorHex
    }
}
