import Foundation

// types.ts → Tab
enum Tab {
    case meetings
    case tasks
    case chat
    case profile
}

// events.ts → NavigateToMeetingEvent.segment
enum MeetingSegment: String, CaseIterable, Identifiable {
    case summary
    case tasks
    case transcript
    case storyline

    var id: String { rawValue }
    var title: String { rawValue.capitalized }
}

/// events.ts → shared navigation state.
/// The TS used a subscribe/notify list plus a `pendingNav` slot because each React component
/// held its own copy of this state. One observable object removes the need for both.
@Observable
final class MeetingNavigator {
    var activeTab: Tab = .meetings
    /// nil = the meetings list is showing.
    var selectedMeetingID: String?
    var activeSegment: MeetingSegment = .summary
    var pendingSeekMilliseconds: Int?


    /// events.ts → navigate(). Also switches to the Meetings tab, which App.tsx did on every event.
    func open(meetingID: String, segment: MeetingSegment = .summary, seekMilliseconds: Int? = nil) {
        selectedMeetingID = meetingID
        activeSegment = segment
        pendingSeekMilliseconds = seekMilliseconds
        activeTab = .meetings
    }

    /// MeetingsTab.tsx → onBack
    func closeMeeting() {
        selectedMeetingID = nil
        activeSegment = .summary
    }
}