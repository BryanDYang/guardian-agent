import SwiftUI

// ChatView.tsx → a single message plus its citation chips.
struct MessageBubble: View {
    let message: ChatMessage

    @Environment(MeetingNavigator.self) private var navigator

    private var isUser: Bool { message.role == .user }

    var body: some View {
        VStack(alignment: isUser ? .trailing : .leading, spacing: 8) {
            Text(message.content)
                .font(.callout)
                .foregroundStyle(isUser ? Color.white : Color.primary)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .frame(maxWidth: 300, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: 18)
                        .fill(isUser ? Color.blue : Color(.systemGray6))
                )

            ForEach(message.citations) { citation in
                Button {
                    navigator.open(meetingID: citation.meetingId, segment: .transcript)
                } label: {
                    Text("\(citation.meetingTitle) @ \(citation.timestamp)")
                        .font(.caption.weight(.semibold))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(
                            Capsule().fill(Color.blue.opacity(0.1))
                        )
                        .overlay(
                            Capsule().strokeBorder(Color.blue.opacity(0.25))
                        )
                }
                .buttonStyle(.plain)
                .foregroundStyle(.blue)
            }
        }
        .frame(maxWidth: .infinity, alignment: isUser ? .trailing : .leading)
    }
}

#Preview {
    VStack(spacing: 24) {
        ForEach(SeedData.mockChat) { message in
            MessageBubble(message: message)
        }
    }
    .padding()
    .environment(MeetingNavigator())
}
