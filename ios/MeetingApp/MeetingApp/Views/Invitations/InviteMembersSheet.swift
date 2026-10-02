import SwiftUI

/// Invite someone to a project by email. The backend returns a link that only
/// works for that email, shared with the system share sheet (FR-INV-4).
struct InviteMembersSheet: View {
    let project: Project

    @Environment(\.dismiss) private var dismiss
    @State private var email = ""
    @State private var link: CreatedInvitation?
    @State private var pending: [RemoteInvitation] = []
    @State private var isWorking = false
    @State private var errorMessage: String?

    private var trimmedEmail: String {
        email.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("name@example.com", text: $email)
                        .textContentType(.emailAddress)
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    Button(isWorking ? "Creating Link..." : "Create Invite Link", action: createLink)
                        .disabled(!trimmedEmail.contains("@") || isWorking)
                } header: {
                    Text("Invite by email")
                } footer: {
                    if let errorMessage {
                        Text(errorMessage).foregroundStyle(Palette.danger)
                    } else {
                        Text("The link works only for this email and expires in 7 days.")
                    }
                }

                if let link {
                    Section {
                        ShareLink(
                            item: link.inviteURL,
                            message: Text(shareMessage(for: link.invitation))
                        ) {
                            Label("Share Invite Link", systemImage: "square.and.arrow.up")
                        }
                    } footer: {
                        Text("Created for \(link.invitation.email).")
                    }
                }

                if !pending.isEmpty {
                    Section("Pending") {
                        ForEach(pending) { invitation in
                            Text(invitation.email)
                                .swipeActions {
                                    Button("Revoke", role: .destructive) {
                                        Task { await revoke(invitation) }
                                    }
                                }
                        }
                    }
                }
            }
            .navigationTitle("Invite to \(project.title)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .task { await loadPending() }
        }
    }

    private func shareMessage(for invitation: RemoteInvitation) -> String {
        "Join \(invitation.projectName) on Meeting Memory. Open this link on your iPhone, "
            + "or sign in as \(invitation.email) and go to Profile > Workspaces."
    }

    private func createLink() {
        isWorking = true
        errorMessage = nil
        Task {
            do {
                link = try await MeetingAPIClient.shared.invite(
                    projectID: project.id, email: trimmedEmail
                )
                email = ""
                await loadPending()
            } catch {
                errorMessage = error.localizedDescription == "already_member"
                    ? "That person is already in this project."
                    : error.localizedDescription
            }
            isWorking = false
        }
    }

    private func loadPending() async {
        if let invitations = try? await MeetingAPIClient.shared.projectInvitations(
            projectID: project.id
        ) {
            pending = invitations
        }
    }

    private func revoke(_ invitation: RemoteInvitation) async {
        do {
            try await MeetingAPIClient.shared.revokeInvitation(
                projectID: project.id, id: invitation.id
            )
            pending.removeAll { $0.id == invitation.id }
            if link?.invitation.id == invitation.id { link = nil }
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}