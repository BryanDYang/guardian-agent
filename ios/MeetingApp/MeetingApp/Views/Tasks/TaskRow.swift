import SwiftUI

/// TasksView.tsx → a single task card. Renders the pending or completed style.
/// Tapping the card expands it to show the full title and where the task came from.
struct TaskRow: View {
    let task: TaskItem
    var isExpanded = false
    var onTap: () -> Void = {}
    let onToggleComplete: () -> Void
    var onEdit: () -> Void = {}
    let onDelete: () -> Void

    private static let avatarSize: CGFloat = 40
    private static let spacing: CGFloat = 12

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            summary
            if isExpanded {
                details
                    .transition(.opacity)
            }
        }
        .padding(12)
        .contentShape(Rectangle())
        .onTapGesture(perform: onTap)
        .accessibilityAction(named: Text(isExpanded ? "Hide details" : "Show details"), onTap)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(task.isCompleted ? Color(.systemGray6) : Color(.systemBackground))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .strokeBorder(Color(.systemGray5))
        )
        .shadow(color: .black.opacity(0.04), radius: 3, y: 1)
        .opacity(task.isCompleted ? 0.6 : 1)
    }

    private var summary: some View {
        HStack(spacing: Self.spacing) {
            AvatarView(
                initials: personInitials,
                colorHex: task.assignee?.colorHex ?? "#9CA3AF",
                size: Self.avatarSize,
                isMuted: task.isCompleted
            )

            VStack(alignment: .leading, spacing: 2) {
                Text(task.title)
                    .font(.subheadline.bold())
                    .foregroundStyle(task.isCompleted ? Color.secondary : Color.primary)
                    .strikethrough(task.isCompleted)
                    .lineLimit(isExpanded ? nil : 1)

                HStack(spacing: 6) {
                    Text(personName)
                        .fontWeight(.medium)
                    Circle().frame(width: 4, height: 4)
                    Text(task.project?.title ?? "")
                }
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(1)
            }

            Spacer(minLength: 8)

            if task.isCompleted {
                Button("Undo", action: onToggleComplete)
                    .font(.caption.bold())
                    .buttonStyle(.plain)
                    .foregroundStyle(.blue)
            } else {
                Button(action: onToggleComplete) {
                    Image(systemName: "checkmark")
                        .font(.footnote.weight(.semibold))
                        .frame(width: 32, height: 32)
                        .background(Circle().fill(Color(.systemGray6)))
                }
                .buttonStyle(.plain)
                .foregroundStyle(.secondary)

                Menu {
                    Button("Edit", systemImage: "pencil", action: onEdit)
                    Button("Move to Trash", systemImage: "trash", role: .destructive, action: onDelete)
                } label: {
                    Image(systemName: "ellipsis")
                        .font(.footnote.weight(.semibold))
                        .frame(width: 32, height: 32)
                        .background(Circle().fill(Color(.systemGray6)))
                }
                .foregroundStyle(.secondary)
                .accessibilityLabel("More actions")
            }
        }
    }

    /// The quote the task came from, then its meeting and timestamp. Indented to
    /// line up with the title.
    private var details: some View {
        VStack(alignment: .leading, spacing: 8) {
            if !task.sourceQuote.isEmpty {
                Text("\u{201C}\(task.sourceQuote)\u{201D}")
                    .font(.footnote)
                    .italic()
                    .foregroundStyle(.secondary)
                    .padding(.leading, 10)
                    .overlay(alignment: .leading) {
                        Capsule()
                            .fill(Color(.systemGray4))
                            .frame(width: 2)
                    }
            }
            Label(sourceLine, systemImage: "waveform")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(.leading, Self.avatarSize + Self.spacing)
    }

    private var sourceLine: String {
        let meeting = task.sourceMeetingTitle.isEmpty ? "Meeting" : task.sourceMeetingTitle
        return task.sourceTimestamp.isEmpty ? meeting : "\(meeting) \u{00B7} \(task.sourceTimestamp)"
    }

    /// A project member first, then a speaker label (SPEAKER_1). Sample tasks
    /// only have a local attendee.
    private var personName: String {
        if let name = task.assigneeName, !name.isEmpty { return name }
        if !task.ownerLabel.isEmpty { return task.ownerLabel }
        if let name = task.assignee?.name, !name.isEmpty { return name }
        return "Unassigned"
    }

    private var personInitials: String {
        if task.assigneeName == nil, let initials = task.assignee?.initials, !initials.isEmpty {
            return initials
        }
        let letters = personName
            .split(separator: " ")
            .prefix(2)
            .compactMap(\.first)
            .map(String.init)
            .joined()
        return letters.isEmpty || personName == "Unassigned" ? "?" : letters.uppercased()
    }
}
