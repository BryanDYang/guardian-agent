import SwiftUI

struct EditProfileSheet: View {
    @Environment(AppSession.self) private var session
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var title = ""

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

                Section("Profile") {
                    TextField("Full name", text: $name)
                        .textContentType(.name)
                    TextField("Title (optional)", text: $title)
                        .textContentType(.jobTitle)
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
                    Button("Save") {
                        session.user.name = trimmedName
                        session.user.title = title.trimmingCharacters(in: .whitespacesAndNewlines)
                        dismiss()
                    }
                    .disabled(trimmedName.isEmpty)
                }
            }
            .onAppear {
                name = session.user.name
                title = session.user.title
            }
        }
    }
}

#Preview {
    EditProfileSheet()
        .environment(AppSession(stage: .signedIn))
}
