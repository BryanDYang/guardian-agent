import SwiftUI

struct FollowupSettingsSheet: View {
    let projectID: String
    @Environment(\.dismiss) private var dismiss
    @State private var settings: RemoteFollowupSettings?
    @State private var emails: [RemoteFollowupEmail] = []
    @State private var emailEnabled = false
    @State private var autoApprove = false
    @State private var receiveEmail = true
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        NavigationStack {
            Form {
                if let settings {
                    Section {
                        Toggle("Email task owners after approval", isOn: $emailEnabled)
                            .disabled(!settings.can_manage || busy)
                        Toggle("Automatically approve clear commitments", isOn: $autoApprove)
                            .disabled(!settings.can_manage || busy)
                        if settings.can_manage {
                            Button("Save project settings") { Task { await saveProject() } }
                                .disabled(busy)
                        }
                    } header: {
                        Text("Project automation")
                    } footer: {
                        Text("Automatic approval is experimental. It requires a confirmed speaker account, an explicit self-commitment, quoted evidence, and no possible duplicate or unresolved deadline. Other tasks stay in review. Enabling it also checks existing candidates.")
                    }
                    Section {
                        Toggle("Receive emails for my tasks", isOn: $receiveEmail)
                        Button("Save my preference") { Task { await savePreference() } }
                            .disabled(busy)
                    } footer: {
                        Text("Messages go to your signed-in account's email address. Recurring reminders are not enabled by this setting.")
                    }
                    Section("Delivery") {
                        Label(settings.delivery_mode == "capture" ? "Test inbox" : "Live email", systemImage: "envelope")
                        Text(settings.delivery_mode == "capture"
                             ? "Messages are captured below. Nothing is sent to anyone's inbox."
                             : "Provider acceptance does not confirm inbox delivery.")
                            .font(.footnote).foregroundStyle(.secondary)
                        Button("Refresh delivery history") { Task { await load() } }
                            .disabled(busy)
                    }
                    Section("Recent follow-ups") {
                        if emails.isEmpty {
                            Text("No follow-ups yet. Enable email, connect a speaker to an app member, then approve a task or use automatic approval.")
                                .foregroundStyle(.secondary)
                        }
                        ForEach(emails) { email in
                            VStack(alignment: .leading, spacing: 6) {
                                Text(email.title).font(.headline)
                                Text(email.recipient_name ?? "Task owner").font(.subheadline)
                                Text(email.status).font(.caption).foregroundStyle(email.state == "failed" ? .red : .secondary)
                                if let message = email.last_error {
                                    Text(message).font(.caption).foregroundStyle(.secondary)
                                }
                                if let preview = email.preview {
                                    DisclosureGroup("Read captured email") {
                                        Text(preview).font(.footnote).textSelection(.enabled)
                                    }
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                } else if busy {
                    ProgressView("Loading follow-through settings")
                }
                if let error {
                    Section {
                        Text(error).foregroundStyle(.red)
                        Button("Retry") { Task { await load() } }
                    }
                }
            }
            .navigationTitle("Follow-through")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
            .task { await load() }
        }
    }

    private func apply(_ value: RemoteFollowupSettings) {
        settings = value
        emailEnabled = value.email_enabled
        autoApprove = value.auto_approve
        receiveEmail = value.receive_email
    }

    private func load() async {
        busy = true
        defer { busy = false }
        do {
            apply(try await MeetingAPIClient.shared.followupSettings(projectID: projectID))
            emails = try await MeetingAPIClient.shared.followupEmails(projectID: projectID)
            error = nil
        } catch { self.error = error.localizedDescription }
    }

    private func saveProject() async {
        busy = true
        defer { busy = false }
        do {
            apply(try await MeetingAPIClient.shared.saveFollowupSettings(projectID: projectID, email: emailEnabled, autoApprove: autoApprove))
            emails = try await MeetingAPIClient.shared.followupEmails(projectID: projectID)
            error = nil
        } catch { self.error = error.localizedDescription }
    }

    private func savePreference() async {
        busy = true
        defer { busy = false }
        do {
            apply(try await MeetingAPIClient.shared.saveFollowupPreference(projectID: projectID, receive: receiveEmail))
            error = nil
        } catch { self.error = error.localizedDescription }
    }
}
