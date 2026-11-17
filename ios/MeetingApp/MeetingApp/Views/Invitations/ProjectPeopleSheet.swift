import SwiftUI

struct ProjectPeopleSheet: View {
    let project: Project

    @Environment(\.dismiss) private var dismiss
    @State private var members: [RemoteMember] = []
    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            List {
                Section {
                    if isLoading {
                        ProgressView("Loading people…")
                    } else if let errorMessage {
                        Text(errorMessage).foregroundStyle(.secondary)
                        Button("Try Again") { Task { await loadMembers() } }
                    } else if members.isEmpty {
                        Text("No members to display.").foregroundStyle(.secondary)
                    } else {
                        ForEach(members) { member in
                            HStack(alignment: .top, spacing: 12) {
                                Image(systemName: "person.crop.circle.fill")
                                    .font(.title2)
                                    .foregroundStyle(.secondary)
                                    .accessibilityHidden(true)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(member.pickerName).font(.headline)
                                    if let name = member.displayName, !name.isEmpty {
                                        Text(member.email)
                                            .font(.subheadline)
                                            .foregroundStyle(.secondary)
                                    }
                                    Text(member.role.capitalized)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                } header: {
                    Text(project.title)
                }
            }
            .navigationTitle("People")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .task { await loadMembers() }
            .refreshable { await loadMembers() }
        }
    }

    @MainActor
    private func loadMembers() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            members = try await MeetingAPIClient.shared.projectMembers(projectID: project.id)
                .sorted { $0.pickerName.localizedStandardCompare($1.pickerName) == .orderedAscending }
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
