import SwiftUI

/// TasksView.tsx → a single task card. Renders the pending or completed style.
struct TaskRow: View {
    let task: TaskItem
    let onToggleComplete: () -> Void
    let onDelete: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            AvatarView(
                initials: task.assignee?.initials ?? "?",
                colorHex: task.assignee?.colorHex ?? "#9CA3AF",
                isMuted: task.isCompleted
            )

            VStack(alignment: .leading, spacing: 2) {
                Text(task.title)
                    .font(.subheadline.bold())
                    .foregroundStyle(task.isCompleted ? Color.secondary : Color.primary)
                    .strikethrough(task.isCompleted)
                    .lineLimit(1)

                HStack(spacing: 6) {
                    Text(task.assignee?.name ?? "Unassigned")
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

                Button(action: onDelete) {
                    Image(systemName: "trash")
                        .font(.footnote.weight(.semibold))
                        .frame(width: 32, height: 32)
                        .background(Circle().fill(Color(.systemGray6)))
                }
                .buttonStyle(.plain)
                .foregroundStyle(.secondary)
            }
        }
        .padding(12)
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
}
