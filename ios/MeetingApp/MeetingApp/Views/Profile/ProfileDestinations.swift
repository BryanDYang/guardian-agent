import SwiftData
import SwiftUI

// Screens pushed from the Profile menu. All content is placeholder until the accounts API exists.

// MARK: - Workspaces

struct WorkspacesView: View {
    @Environment(\.modelContext) private var context
    @State private var invitations: [RemoteInvitation] = []
    @State private var workspaces = ProfilePlaceholder.workspaces
    @State private var errorMessage: String?

    var body: some View {
        List {
            if let errorMessage {
                Section {
                    Text(errorMessage)
                        .font(.footnote)
                        .foregroundStyle(Palette.danger)
                }
            }

            if !invitations.isEmpty {
                Section("Pending invitations") {
                    ForEach(invitations) { invite in
                        VStack(alignment: .leading, spacing: 10) {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(invite.projectName)
                                    .font(.subheadline.weight(.semibold))
                                Text("Invited by \(invite.invitedByName ?? "a teammate")")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            HStack {
                                Button("Decline") {
                                    Task { await respond(to: invite, accepted: false) }
                                }
                                .buttonStyle(.bordered)
                                Button("Accept") {
                                    Task { await respond(to: invite, accepted: true) }
                                }
                                .buttonStyle(.borderedProminent)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }
            }

            Section("Your workspaces") {
                ForEach(workspaces) { workspace in
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(workspace.name)
                                .font(.subheadline.weight(.semibold))
                            Text("\(workspace.memberCount) members \u{2022} Active \(workspace.lastActivity)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        RoleBadge(role: workspace.role)
                    }
                }
            }
        }
        .navigationTitle("Workspaces")
        .task { await loadInvitations() }
        .refreshable { await loadInvitations() }
    }

    private func loadInvitations() async {
        do {
            invitations = try await MeetingAPIClient.shared.myInvitations()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func respond(to invite: RemoteInvitation, accepted: Bool) async {
        do {
            if accepted {
                _ = try await MeetingAPIClient.shared.acceptInvitation(id: invite.id)
                try? await ProjectSync.refreshProjects(context: context, api: .shared)
            } else {
                try await MeetingAPIClient.shared.declineInvitation(id: invite.id)
            }
            invitations.removeAll { $0.id == invite.id }
        } catch {
            errorMessage = InviteErrors.message(for: error)
        }
    }
}

private struct RoleBadge: View {
    let role: String

    var body: some View {
        let isOwner = role == "Owner"
        Text(role)
            .font(.caption2.weight(.semibold))
            .foregroundStyle(isOwner ? Palette.violet : Palette.secondaryText)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(Capsule().fill(isOwner ? Palette.violetWash : Palette.fieldFill))
            .overlay(Capsule().strokeBorder(isOwner ? Palette.violet.opacity(0.3) : Palette.border))
    }
}

// MARK: - Speaker identity

struct SpeakerIdentityView: View {
    @Environment(AppSession.self) private var session
    @State private var showingRecorder = false
    @State private var confirmingRevoke = false

    var body: some View {
        List {
            Section {
                if let enrolledAt = session.user.voiceprintEnrolledAt {
                    LabeledContent {
                        Text(enrolledAt.formatted(date: .abbreviated, time: .omitted))
                    } label: {
                        Label("Voiceprint enrolled", systemImage: "checkmark.seal.fill")
                            .foregroundStyle(Palette.success)
                    }
                } else {
                    Label("Not enrolled", systemImage: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                }

                Button(session.user.hasVoiceprint ? "Re-record voice sample" : "Record voice sample") {
                    showingRecorder = true
                }
            } header: {
                Text("Voiceprint")
            } footer: {
                Text("Used only to label you in meetings of projects you belong to. Unrecognized voices appear as SPEAKER_1, SPEAKER_2, and so on.")
            }

            if session.user.hasVoiceprint {
                Section("Attendee mapping") {
                    ForEach(ProfilePlaceholder.speakerMappings) { mapping in
                        LabeledContent(mapping.projectName) {
                            Text("Recognized in \(mapping.recognizedMeetings) meetings")
                        }
                    }
                }

                Section {
                    Button("Revoke consent & delete voiceprint", role: .destructive) {
                        confirmingRevoke = true
                    }
                }
            }
        }
        .navigationTitle("Speaker Identity")
        .fullScreenCover(isPresented: $showingRecorder) {
            VoiceEnrollmentView(
                speakerName: session.user.name,
                skipTitle: "Cancel",
                onFinish: {
                    session.user.voiceprintEnrolledAt = .now
                    showingRecorder = false
                },
                onSkip: { showingRecorder = false }
            )
        }
        .confirmationDialog("Delete your voiceprint?", isPresented: $confirmingRevoke, titleVisibility: .visible) {
            Button("Revoke & Delete", role: .destructive) {
                session.user.voiceprintEnrolledAt = nil
            }
        } message: {
            Text("You'll appear as SPEAKER_N in future meetings until you record again.")
        }
    }
}

// MARK: - Notifications & integrations

struct NotificationsIntegrationsView: View {
    @Environment(\.openURL) private var openURL
    @State private var notifyInvites = true
    @State private var notifyMeetingProcessed = true
    @State private var notifyTasksDue = true

    var body: some View {
        List {
            Section("Integrations") {
                LabeledContent {
                    Text("Connected")
                } label: {
                    Label("Apple Reminders", systemImage: "checklist")
                }
                LabeledContent {
                    Text("Connected")
                } label: {
                    Label("Calendar", systemImage: "calendar")
                }
                Button("Manage in Settings") {
                    if let url = URL(string: UIApplication.openSettingsURLString) {
                        openURL(url)
                    }
                }
            }

            Section("Push alerts") {
                Toggle("Workspace invitations", isOn: $notifyInvites)
                Toggle("Meeting finished processing", isOn: $notifyMeetingProcessed)
                Toggle("Tasks due soon", isOn: $notifyTasksDue)
            }
        }
        .navigationTitle("Notifications")
    }
}

// MARK: - Privacy & data

struct PrivacyDataView: View {
    @State private var showingExportAlert = false
    @State private var showingDeleteAccount = false

    var body: some View {
        List {
            Section {
                Button {
                    showingExportAlert = true
                } label: {
                    Label("Export my data", systemImage: "square.and.arrow.up")
                }
            } footer: {
                Text("Get a copy of your meetings, transcripts, tasks, and chat history.")
            }

            Section("Policies") {
                Link(destination: ProfilePlaceholder.voiceConsentURL) {
                    Label("Voice consent", systemImage: "waveform")
                }
                Link(destination: ProfilePlaceholder.privacyURL) {
                    Label("Privacy Policy", systemImage: "hand.raised")
                }
            }

            Section {
                Button("Delete account", role: .destructive) {
                    showingDeleteAccount = true
                }
            } footer: {
                Text("Permanently deletes your account, voiceprint, and memberships. Meetings in projects shared with others stay with those projects.")
            }
        }
        .navigationTitle("Privacy & Data")
        .alert("Export requested", isPresented: $showingExportAlert) {
            Button("OK", role: .cancel) {}
        } message: {
            Text("We'll prepare your data export.")
        }
        .sheet(isPresented: $showingDeleteAccount) {
            DeleteAccountView()
        }
    }
}

// MARK: - Security & credentials

struct SecurityCredentialsView: View {
    @Environment(AppSession.self) private var session

    var body: some View {
        List {
            Section("Sign-in methods") {
                LabeledContent {
                    Text(session.user.signInMethod == .email ? "Primary" : "Not set")
                } label: {
                    Label("Email & password", systemImage: "envelope")
                }
                LabeledContent {
                    Text(session.user.signInMethod == .google ? "Connected" : "Not connected")
                } label: {
                    Label("Google", systemImage: "g.circle")
                }
            }

            if session.user.signInMethod == .email {
                Section {
                    NavigationLink("Change password") {
                        ChangePasswordView()
                    }
                }
            }

            Section("Active sessions") {
                LabeledContent {
                    Text("Active now")
                } label: {
                    Label("This iPhone", systemImage: "iphone")
                }
            }
        }
        .navigationTitle("Security")
    }
}

private struct ChangePasswordView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var currentPassword = ""
    @State private var newPassword = ""
    @State private var confirmPassword = ""

    private var canSave: Bool {
        !currentPassword.isEmpty && newPassword.count >= 6 && newPassword == confirmPassword
    }

    var body: some View {
        Form {
            SecureField("Current password", text: $currentPassword)
                .textContentType(.password)
            SecureField("New password", text: $newPassword)
                .textContentType(.newPassword)
            SecureField("Confirm new password", text: $confirmPassword)
                .textContentType(.newPassword)
        }
        .navigationTitle("Change Password")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .confirmationAction) {
                // Placeholder: no API call yet.
                Button("Save") { dismiss() }
                    .disabled(!canSave)
            }
        }
    }
}

// MARK: - About

struct AboutView: View {
    var body: some View {
        List {
            Section {
                LabeledContent("Version", value: "\(ProfilePlaceholder.appVersion) (\(ProfilePlaceholder.buildNumber))")
            }

            Section {
                Link("Terms of Service", destination: ProfilePlaceholder.termsURL)
                Link("Privacy Policy", destination: ProfilePlaceholder.privacyURL)
                Link("Contact Support", destination: ProfilePlaceholder.supportURL)
            }
        }
        .navigationTitle("About")
    }
}

#Preview("Workspaces") {
    NavigationStack { WorkspacesView() }
}

#Preview("Speaker Identity") {
    NavigationStack { SpeakerIdentityView() }
        .environment(AppSession(stage: .signedIn))
}
