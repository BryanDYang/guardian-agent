import SwiftUI

/// Onboarding step 1 (FR-ONB-1): shown when the account has no display name yet.
struct ProfileSetupView: View {
    @Environment(AppSession.self) private var session
    @State private var name = ""
    @State private var title = ""
    @State private var isWorking = false
    @State private var errorMessage: String?

    private var trimmedName: String {
        name.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                AuthBrandHeader(subtitle: "Tell your teammates who you are")
                    .padding(.top, 24)

                VStack(spacing: 18) {
                    AuthField(
                        "Full name",
                        icon: "person",
                        placeholder: "Alex Rivera",
                        text: $name,
                        contentType: .name
                    )
                    AuthField(
                        "Title (optional)",
                        icon: "briefcase",
                        placeholder: "PhD student",
                        text: $title,
                        contentType: .jobTitle
                    )

                    if let errorMessage {
                        Text(errorMessage)
                            .font(.footnote)
                            .foregroundStyle(Palette.danger)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding(.top, 48)

                Button(isWorking ? "Saving..." : "Continue", action: save)
                    .buttonStyle(PrimaryButtonStyle())
                    .disabled(trimmedName.isEmpty || isWorking)
                    .padding(.top, 24)
            }
            .padding(.horizontal, 20)
        }
        .scrollBounceBehavior(.basedOnSize)
        .background(Color.white)
    }

    private func save() {
        isWorking = true
        errorMessage = nil
        Task {
            do {
                try await session.saveProfile(
                    name: trimmedName,
                    title: title.trimmingCharacters(in: .whitespacesAndNewlines)
                )
            } catch {
                errorMessage = error.localizedDescription
            }
            isWorking = false
        }
    }
}

#Preview {
    ProfileSetupView()
        .environment(AppSession(stage: .profileSetup))
}
