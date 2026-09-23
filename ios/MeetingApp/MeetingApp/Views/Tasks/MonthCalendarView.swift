import SwiftUI

/// TasksView.tsx → the calendar widget (month title, arrows, weekday row, 42-cell grid).
struct MonthCalendarView: View {
    /// Any date inside the month being displayed.
    @Binding var month: Date
    @Binding var selectedDate: Date
    /// Whether a dot should be drawn under a given day.
    let hasTask: (Date) -> Bool

    private let calendar = Calendar.current
    private let weekdaySymbols = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    private let columns = Array(repeating: GridItem(.flexible(), spacing: 0), count: 7)

    var body: some View {
        VStack(spacing: 8) {
            monthHeader
            weekdayHeader
            grid
        }
    }

    private var monthHeader: some View {
        HStack {
            Button { shiftMonth(by: -1) } label: {
                Image(systemName: "chevron.left").font(.title3.weight(.semibold))
            }
            Spacer()
            Text(monthTitle)
                .font(.title2.bold())
                .foregroundStyle(.primary)
            Spacer()
            Button { shiftMonth(by: 1) } label: {
                Image(systemName: "chevron.right").font(.title3.weight(.semibold))
            }
        }
        .foregroundStyle(.red)
        .padding(.bottom, 4)
    }

    private var weekdayHeader: some View {
        HStack(spacing: 0) {
            ForEach(Array(weekdaySymbols.enumerated()), id: \.offset) { index, symbol in
                Text(symbol)
                    .font(.system(size: 10, weight: .bold))
                    .kerning(0.5)
                    .foregroundStyle(index == 0 || index == 6 ? Color.secondary : Color.blue)
                    .frame(maxWidth: .infinity)
            }
        }
    }

    private var grid: some View {
        LazyVGrid(columns: columns, spacing: 8) {
            ForEach(Array(cells.enumerated()), id: \.offset) { _, date in
                if let date {
                    dayCell(date)
                } else {
                    Color.clear.frame(height: 40)
                }
            }
        }
    }

    private func dayCell(_ date: Date) -> some View {
        let isSelected = calendar.isDate(date, inSameDayAs: selectedDate)
        let isToday = calendar.isDateInToday(date)

        return Button {
            selectedDate = calendar.startOfDay(for: date)
        } label: {
            VStack(spacing: 2) {
                Text("\(calendar.component(.day, from: date))")
                    .font(.system(size: 15, weight: isToday && !isSelected ? .bold : .medium))
                    .foregroundStyle(isSelected ? Color.white : (isToday ? Color.blue : Color.primary))
                    .frame(width: 32, height: 32)
                    .background(Circle().fill(isSelected ? Color.blue : Color.clear))

                Circle()
                    .fill(isSelected ? Color.white : Color.green)
                    .frame(width: 4, height: 4)
                    .opacity(hasTask(date) ? 1 : 0)
            }
            .frame(height: 40)
        }
        .buttonStyle(.plain)
    }

    // MARK: Date math

    private var monthGrid: MonthGrid {
        MonthGrid(month: month, calendar: calendar)
    }

    private var monthTitle: String { monthGrid.title }

    private var cells: [Date?] { monthGrid.cells }

    private func shiftMonth(by value: Int) {
        month = monthGrid.shifted(by: value)
    }
}


private struct MonthCalendarPreview: View {
    @State private var month = Date()
    @State private var selected = Calendar.current.startOfDay(for: .now)

    var body: some View {
        MonthCalendarView(month: $month, selectedDate: $selected) { date in
            Calendar.current.component(.day, from: date) % 5 == 0
        }
        .padding()
    }
}

#Preview {
    MonthCalendarPreview()
}
