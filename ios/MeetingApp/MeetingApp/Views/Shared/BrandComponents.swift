import SwiftUI

/// Conversation-to-action mark, shared with the Home Screen icon.
struct AppMark: View {
    var size: CGFloat = 56

    var body: some View {
        Image("BrandMark")
            .resizable()
            .interpolation(.high)
            .scaledToFit()
            .frame(width: size, height: size)
            .clipShape(RoundedRectangle(cornerRadius: size * 0.23, style: .continuous))
            .accessibilityHidden(true)
    }
}

/// Solid blue full-width button ("Log In", "Create Account", "Press to Record Voice Sample").
/// Fades when disabled, like the record button before consent is checked.
struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        PrimaryButtonBody(configuration: configuration)
    }

    private struct PrimaryButtonBody: View {
        let configuration: ButtonStyleConfiguration
        @Environment(\.isEnabled) private var isEnabled

        var body: some View {
            configuration.label
                .font(.headline)
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity, minHeight: 50)
                .background(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(Palette.brandBlue.opacity(isEnabled ? 1 : 0.55))
                )
                .shadow(color: Palette.brandBlue.opacity(isEnabled ? 0.3 : 0), radius: 8, y: 4)
                .opacity(configuration.isPressed ? 0.85 : 1)
        }
    }
}

/// White full-width button with a border ("Continue with Google", "Sign Out").
struct OutlineButtonStyle: ButtonStyle {
    var tint: Color = Palette.ink
    var borderColor: Color = Palette.border

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.subheadline.weight(.semibold))
            .foregroundStyle(tint)
            .frame(maxWidth: .infinity, minHeight: 50)
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(configuration.isPressed ? Palette.fieldFill : .white)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .strokeBorder(borderColor, lineWidth: 1.5)
            )
    }
}

struct GoogleButton: View {
    let title: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                // Placeholder mark. Swap in the official "G" asset from Google's sign-in branding kit.
                Text("G")
                    .font(.system(size: 18, weight: .bold))
                    .foregroundStyle(Palette.brandBlue)
                    .accessibilityHidden(true)
                Text(title)
            }
        }
        .buttonStyle(OutlineButtonStyle())
    }
}

#Preview {
    VStack(spacing: 16) {
        AppMark()
        GoogleButton(title: "Continue with Google") {}
        Button("Log In") {}.buttonStyle(PrimaryButtonStyle())
        Button("Disabled") {}.buttonStyle(PrimaryButtonStyle()).disabled(true)
        Button("Sign Out") {}
            .buttonStyle(OutlineButtonStyle(tint: Palette.danger, borderColor: Palette.dangerBorder))
    }
    .padding()
}
