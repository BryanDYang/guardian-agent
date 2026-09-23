import SwiftUI
import SwiftData

// MeetingDetailView.tsx → activeSegment === 'summary'
struct SummarySegment: View {
    let meeting: Meeting

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            section("EXECUTIVE SUMMARY") {
                VStack(alignment: .leading, spacing: 12) {
                    ForEach(Array(meeting.summary.enumerated()), id: \.offset) { _, line in
                        HStack(alignment: .top, spacing: 12) {
                            Circle()
                                .fill(Color.blue)
                                .frame(width: 6, height: 6)
                                .padding(.top, 6)
                            Text(line)
                                .font(.subheadline)
                                .foregroundStyle(.primary)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(16)
                .background(card)
            }

            section("DECISIONS REACHED") {
                VStack(spacing: 8) {
                    ForEach(Array(meeting.decisions.enumerated()), id: \.element.id) { index, decision in
                        HStack(alignment: .top, spacing: 12) {
                            Text("\(index + 1).")
                                .font(.subheadline.weight(.semibold))
                                .foregroundStyle(.secondary)

                            Text(decision.text)
                                .font(.subheadline)
                                .frame(maxWidth: .infinity, alignment: .leading)

                            Text("[\(decision.timestamp)]")
                                .font(.caption.monospaced())
                                .foregroundStyle(.secondary)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 3)
                                .background(
                                    RoundedRectangle(cornerRadius: 6)
                                        .fill(Color(.systemGray6))
                                )
                        }
                        .padding(16)
                        .background(card)
                    }
                }
            }
        }
    }

    private func section<Content: View>(
        _ title: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.caption.weight(.semibold))
                .kerning(0.5)
                .foregroundStyle(.secondary)
            content()
        }
    }

    private var card: some View {
        RoundedRectangle(cornerRadius: 12)
            .fill(Color(.systemBackground))
            .shadow(color: .black.opacity(0.03), radius: 4, y: 1)
    }
}

#Preview {
    SummarySegmentPreview()
        .modelContainer(PreviewContainer.shared)
}

private struct SummarySegmentPreview: View {
    @Query private var meetings: [Meeting]

    var body: some View {
        ScrollView {
            if let meeting = meetings.first(where: { $0.id == "m1" }) {
                SummarySegment(meeting: meeting).padding(16)
            }
        }
        .background(Color(.systemGroupedBackground))
    }
}
