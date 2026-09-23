import Foundation

/// The 42-cell month layout behind MonthCalendarView, with no SwiftUI in it.
struct MonthGrid {
    static let cellCount = 42

    /// Any date inside the month being laid out.
    let month: Date
    var calendar: Calendar = .current

    var start: Date {
        calendar.date(from: calendar.dateComponents([.year, .month], from: month)) ?? month
    }

    var dayCount: Int {
        calendar.range(of: .day, in: .month, for: start)?.count ?? 0
    }

    /// Empty cells before the 1st. Weekday 1 is Sunday, so the grid is always Sunday-first.
    var leadingBlanks: Int {
        calendar.component(.weekday, from: start) - 1
    }

    var cells: [Date?] {
        let days: [Date?] = (0..<dayCount).map {
            calendar.date(byAdding: .day, value: $0, to: start)
        }
        let filled: [Date?] = Array(repeating: nil, count: leadingBlanks) + days
        return filled + Array(repeating: nil, count: max(0, Self.cellCount - filled.count))
    }

    var title: String {
        month.formatted(.dateTime.month(.wide))
    }

    /// Steps whole months, rolling the year over at the boundaries.
    func shifted(by months: Int) -> Date {
        calendar.date(byAdding: .month, value: months, to: start) ?? start
    }
}
