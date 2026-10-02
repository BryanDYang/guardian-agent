import SwiftData
import SwiftUI

/// Opened from meetingmemory://invite?token=... once the user is signed in and
/// onboarded. Accepting adds them to the project (FR-INV-6, FR-INV-7).
struct InviteLinkSheet: View {
    let token: String

    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var context
    @State private var isWorking = false
    @State private var joinedProject: String?
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: joinedProject == nil ? "person.badge.plus" : "checkmark.circle.fill")
                .font(.system(size: 48))
                .foregroundStyle(Palette.brandBlue)
                .padding(.top, 32)

            Text(joinedProject.map { "You joined \($0)" } ?? "Join a project?")
                .font(.title2.bold())

            Text(joinedProject == nil
                 ? "You were invited to a project on Meeting Memory. Accept to see its meetings, tasks, and chats."
                 : "It's now in your Projects list.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            if let errorMessage {
                Text(errorMessage)
                    .font(.footnote)
                    .foregroundStyle(Palette.danger)
                    .multilineTextAlignment(.center)
            }

            Spacer()

            if joinedProject == nil {
                Button(isWorking ? "Joining..." : "Accept Invite", action: accept)
                    .buttonStyle(PrimaryButtonStyle())
                    .disabled(isWorking)
                Button("Not Now") { dismiss() }
                    .font(.footnote)
            } else {
                Button("Done") { dismiss() }
                    .buttonStyle(PrimaryButtonStyle())
            }
        }
        .padding(24)
        .presentationDetents([.medium])
    }

    private func accept() {
        isWorking = true
        errorMessage = nil
        Task {
            do {
                let joined = try await MeetingAPIClient.shared.acceptInvitation(token: token)
                // Bring the new project into the Projects list right away.
                try? await ProjectSync.refreshProjects(context: context, api: .shared)
                joinedProject = joined.projectName
            } catch {
                errorMessage = InviteErrors.message(for: error)
            }
            isWorking = false
        }
    }
}