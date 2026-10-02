import SwiftUI

struct SignUpView: View {
    let onLogIn: () -> Void

    @Environment(AppSession.self) private var session
    @State private var fullName = ""
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var isWorking = false
    @State private var errorMessage: String?
    @State private var showingCheckEmail = false

    private static let minimumPasswordLength = 6

    private var trimmedName: String {
        fullName.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var passwordsMismatch: Bool {
        !confirmPassword.isEmpty && password != confirmPassword
    }

    private var canSubmit: Bool {
        !trimmedName.isEmpty
            && email.contains("@")
            && password.count >= Self.minimumPasswordLength
            && password == confirmPassword
    }

    var body: some View {
        VStack(spacing: 0) {
            ScrollView {
                VStack(spacing: 0) {
                    HStack {
                        Button(action: onLogIn) {
                            Label("Back", systemImage: "arrow.left")
                                .font(.subheadline.weight(.medium))
                                .foregroundStyle(Palette.secondaryText)
                        }
                        .buttonStyle(.plain)
                        Spacer()
                    }
                    .padding(.top, 8)

                    AuthBrandHeader(subtitle: "Create an account to start syncing meetings")
                        .padding(.top, 16)

                    VStack(spacing: 18) {
                        AuthField(
                            "Full name",
                            icon: "person",
                            placeholder: "e.g. John Doe",
                            text: $fullName,
                            contentType: .name
                        )

                        AuthField(
                            "Email address",
                            icon: "envelope",
                            placeholder: "name@example.com",
                            text: $email,
                            contentType: .emailAddress,
                            keyboard: .emailAddress
                        )

                        AuthField(
                            "Password",
                            icon: "lock",
                            placeholder: "At least \(Self.minimumPasswordLength) characters",
                            text: $password,
                            isSecure: true,
                            contentType: .newPassword
                        )

                        VStack(alignment: .leading, spacing: 6) {
                            AuthField(
                                "Confirm password",
                                icon: "lock",
                                placeholder: "Repeat password",
                                text: $confirmPassword,
                                isSecure: true,
                                contentType: .newPassword
                            )
                            if passwordsMismatch {
                                Text("Passwords don't match.")
                                    .font(.caption)
                                    .foregroundStyle(Palette.danger)
                            }
                        }

                        if let errorMessage {
                            Text(errorMessage)
                                .font(.footnote)
                                .foregroundStyle(Palette.danger)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    .padding(.top, 40)

                    VStack(spacing: 14) {
                        GoogleButton(title: "Sign up with Google") {
                            errorMessage = "Google sign-in isn't set up yet."
                        }

                        Button(isWorking ? "Creating Account..." : "Create Account", action: createAccount)
                            .buttonStyle(PrimaryButtonStyle())
                            .disabled(!canSubmit || isWorking)
                    }
                    .padding(.top, 20)
                }
                .padding(.horizontal, 20)
            }
            .scrollBounceBehavior(.basedOnSize)

            AuthFooter(prompt: "Already have an account?", actionTitle: "Log in", action: onLogIn)
                .padding(.horizontal, 20)
                .padding(.bottom, 12)
        }
        .background(Color.white)
        .alert("Check your email", isPresented: $showingCheckEmail) {
            Button("OK", action: onLogIn)
        } message: {
            Text("We sent a confirmation link to \(email). Open it, then log in.")
        }
    }

    private func createAccount() {
        isWorking = true
        errorMessage = nil
        Task {
            do {
                let needsConfirmation = try await session.signUp(
                    name: trimmedName,
                    email: email.trimmingCharacters(in: .whitespacesAndNewlines),
                    password: password
                )
                if needsConfirmation {
                    showingCheckEmail = true
                }
            } catch {
                errorMessage = error.localizedDescription
            }
            isWorking = false
        }
    }
}

#Preview {
    SignUpView(onLogIn: {})
        .environment(AppSession())
}
