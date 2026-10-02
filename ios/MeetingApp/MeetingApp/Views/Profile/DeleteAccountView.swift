import SwiftUI

/// FR-ACCT-1: account deletion behind a typed confirmation.
struct DeleteAccountView: View {
    @Environment(AppSession.self) private var session
    @Environment(\.dismiss) private var dismiss
    @State private var confirmation = ""
    @State private var isDeleting = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Label("Your account, profile, and sign-in", systemImage: "person.crop.circle.badge.xmark")
                    Label("Projects where you're the only member, with their recordings, transcripts, tasks, and chats", systemImage: "folder.badge.minus")
                    Label("Your chats and your memberships in shared projects", systemImage: "bubble.left.and.bubble.right")
                    Label("Invitations you sent that are still pending", systemImage: "envelope.badge")
                } header: {
                    Text("This deletes")
                } footer: {
                    Text("Meetings and tasks in projects shared with others stay with those projects, without your name. This can't be undone.")
                }

                Section {
                    TextField("Type DELETE", text: $confirmation)
                        .textInputAutocapitalization(.characters)
                        .autocorrectionDisabled()
                        .disabled(isDeleting)
                } footer: {
                    if let errorMessage {
                        Text(errorMessage)
                            .foregroundStyle(Palette.danger)
                    }
                }

                Section {
                    Button(role: .destructive, action: delete) {
                        if isDeleting {
                            HStack(spacing: 8) {
                                ProgressView()
                                Text("Deleting...")
                            }
                        } else {
                            Text("Delete My Account")
                        }
                    }
                    .disabled(confirmation != "DELETE" || isDeleting)
                }
            }
            .navigationTitle("Delete Account")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .disabled(isDeleting)
                }
            }
            .interactiveDismissDisabled(isDeleting)
        }
    }

    private func delete() {
        isDeleting = true
        errorMessage = nil
        Task {
            do {
                try await session.deleteAccount()
                // Signed out: the app switches to Log In and this sheet goes with it.
            } catch {
                errorMessage = error.localizedDescription
                isDeleting = false
            }
        }
    }
}

#Preview {
    DeleteAccountView()
        .environment(AppSession(stage: .signedIn))
}