import SwiftUI

struct LoginView: View {
    let onCreateAccount: () -> Void

    @Environment(AppSession.self) private var session
    @State private var email = ""
    @State private var password = ""
    @State private var showingResetAlert = false

    private var canSubmit: Bool {
        email.contains("@") && !password.isEmpty
    }

    var body: some View {
        VStack(spacing: 0) {
            ScrollView {
                VStack(spacing: 0) {
                    AuthBrandHeader(subtitle: "Sign in to access your projects and tasks")
                        .padding(.top, 24)

                    VStack(spacing: 18) {
                        AuthField(
                            "Email",
                            icon: "envelope",
                            placeholder: "name@example.com",
                            text: $email,
                            contentType: .emailAddress,
                            keyboard: .emailAddress
                        )

                        AuthField(
                            "Password",
                            icon: "lock",
                            placeholder: "Your password",
                            text: $password,
                            isSecure: true,
                            contentType: .password
                        ) {
                            Button("Forgot password?") { showingResetAlert = true }
                                .font(.footnote.weight(.semibold))
                                .foregroundStyle(Palette.brandBlue)
                        }
                    }
                    .padding(.top, 72)

                    VStack(spacing: 14) {
                        GoogleButton(title: "Continue with Google") {
                            session.continueWithGoogle(isNewAccount: false)
                        }

                        Button("Log In") { session.logIn(email: email) }
                            .buttonStyle(PrimaryButtonStyle())
                            .disabled(!canSubmit)
                    }
                    .padding(.top, 24)
                }
                .padding(.horizontal, 20)
            }
            .scrollBounceBehavior(.basedOnSize)

            AuthFooter(prompt: "Don't have an account?", actionTitle: "Create account", action: onCreateAccount)
                .padding(.horizontal, 20)
                .padding(.bottom, 12)
        }
        .background(Color.white)
        .alert("Reset your password", isPresented: $showingResetAlert) {
            Button("OK", role: .cancel) {}
        } message: {
            // Placeholder: the real flow calls Supabase resetPasswordForEmail.
            Text(email.isEmpty
                 ? "Enter your email above, then tap Forgot password again."
                 : "If an account exists for \(email), we sent a reset link.")
        }
    }
}

#Preview {
    LoginView(onCreateAccount: {})
        .environment(AppSession())
}
