import SwiftUI

// MeetingDetailView.tsx → the "Privacy & Governance" bottom sheet.
// Both actions were no-ops in the TS and stay no-ops here.
struct PrivacySettingsSheet: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Button("Open Redaction Tool") { }
                } header: {
                    Text("Selective Redaction")
                } footer: {
                    Text("Select sensitive transcript segments to permanently strike from the RAG indexing pipeline.")
                }

                Section {
                    Button("Purge Project Data", role: .destructive) { }
                } header: {
                    Text("Project-Scoped Purge")
                        .foregroundStyle(.red)
                } footer: {
                    Text("Permanently delete all vector embeddings, transcripts, and securely clear raw audio files for this project. This action cannot be undone.")
                }
            }
            .navigationTitle("Privacy & Governance")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
        .presentationDetents([.medium, .large])
    }
}

#Preview {
    PrivacySettingsSheet()
}
