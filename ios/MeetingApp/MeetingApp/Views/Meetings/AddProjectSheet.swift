import SwiftUI
import SwiftData

// MeetingsListView.tsx → the "Add Project" modal.
struct AddProjectSheet: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var context

    @State private var name = ""

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
            }
            .navigationTitle("Add Project")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") { addProject() }
                        .disabled(trimmedName.isEmpty)
                }
            }
        }
        .presentationDetents([.medium])
    }

    private var trimmedName: String {
        name.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func addProject() {
        let project = Project(
            id: UUID().uuidString,
            title: trimmedName,
            colorHex: Self.palette.randomElement() ?? "#5E5CE6",
            iconSystemName: "folder",
            createdAt: .now
        )
        context.insert(project)
        dismiss()
    }
}

#Preview {
    AddProjectSheet()
        .modelContainer(PreviewContainer.shared)
}
