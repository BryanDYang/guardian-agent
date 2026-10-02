import SwiftUI

struct EditProfileSheet: View {
    @Environment(AppSession.self) private var session
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var title = ""
    @State private var isSaving = false
    @State private var errorMessage: String?

    private var trimmedName: String {
        name.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    VStack(spacing: 10) {
                        Text(trimmedName.first.map { String($0).uppercased() } ?? session.user.initial)
                            .font(.largeTitle.weight(.semibold))
                            .foregroundStyle(.white)
                            .frame(width: 80, height: 80)
                            .background(RoundedRectangle(cornerRadius: 20, style: .continuous).fill(Palette.brandBlue))
                        // Placeholder: photo picker not wired up.
                        Button("Change photo") {}
                            .font(.subheadline.weight(.semibold))
                    }
                    .frame(maxWidth: .infinity)
                }
                .listRowBackground(Color.clear)

                Section {
                    TextField("Full name", text: $name)
                        .textContentType(.name)
                    TextField("Title (optional)", text: $title)
                        .textContentType(.jobTitle)
                } header: {
                    Text("Profile")
                } footer: {
                    if let errorMessage {
                        Text(errorMessage).foregroundStyle(Palette.danger)
                    }
                }

                Section {
                    LabeledContent("Email", value: session.user.email)
                } footer: {
                    Text("Your email is used to match workspace invitations.")
                }
            }
            .navigationTitle("Edit Profile")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(isSaving ? "Saving..." : "Save", action: save)
                        .disabled(trimmedName.isEmpty || isSaving)
                }
            }
            .onAppear {
                name = session.user.name
                title = session.user.title
            }
        }
    }

    private func save() {
        isSaving = true
        errorMessage = nil
        Task {
            do {
                try await session.updateProfile(
                    name: trimmedName,
                    title: title.trimmingCharacters(in: .whitespacesAndNewlines)
                )
                dismiss()
            } catch {
                errorMessage = error.localizedDescription
                isSaving = false
            }
        }
    }
}

#Preview {
    EditProfileSheet()
        .environment(AppSession(stage: .signedIn))
}
