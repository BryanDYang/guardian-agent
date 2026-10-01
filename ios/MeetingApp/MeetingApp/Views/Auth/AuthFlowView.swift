import SwiftUI

/// Signed-out root: switches between Log In and Sign Up.
struct AuthFlowView: View {
    @State private var showingSignUp = false

    var body: some View {
        Group {
            if showingSignUp {
                SignUpView(onLogIn: { showingSignUp = false })
                    .transition(.move(edge: .trailing))
            } else {
                LoginView(onCreateAccount: { showingSignUp = true })
                    .transition(.move(edge: .leading))
            }
        }
        .animation(.easeInOut(duration: 0.25), value: showingSignUp)
    }
}

#Preview {
    AuthFlowView()
        .environment(AppSession())
}
