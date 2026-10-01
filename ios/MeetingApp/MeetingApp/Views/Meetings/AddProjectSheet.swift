import SwiftUI
import SwiftData

// MeetingsListView.tsx → the "Add Project" modal.
struct AddProjectSheet: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var context

    @State private var name = ""
    @State private var isSaving = false
    @State private var errorMessage: String?

    /// New projects need a color; the TS modal didn't ask for one.
    private static let palette = ["#5E5CE6", "#34C759", "#FF9500", "#FF3B30", "#32ADE6"]

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("e.g. Thesis Research", text: $name)
                } header: {
                    Text("Project Details")
                } footer: {
                    Text("Create a new workspace for your meetings.")
                }

                if isSaving {
                    Section {
                        HStack {
                            ProgressView()
                            Text("Saving project…")
                        }
                    }
                }

                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("Add Project")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .disabled(isSaving)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") {
                        Task { await addProject() }
                    }
                    .disabled(trimmedName.isEmpty || isSaving)
                }
            }
        }
        .presentationDetents([.medium])
        .interactiveDismissDisabled(isSaving)
    }

    private var trimmedName: String {
        name.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    @MainActor
    private func addProject() async {
        isSaving = true
        errorMessage = nil
        defer { isSaving = false }

        do {
            let remote = try await MeetingAPIClient.shared.createProject(name: trimmedName)
            let project = Project(
                id: remote.id,
                title: ProjectSync.displayName(remote.name),
                colorHex: ProjectSync.sampleColor(remote.name) ?? Self.palette.randomElement() ?? "#5E5CE6",
                iconSystemName: "folder",
                createdAt: .now
            )
            context.insert(project)
            try context.save()
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    AddProjectSheet()
        .modelContainer(PreviewContainer.shared)
}
