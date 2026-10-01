import SwiftUI

/// Logo, app name, and subtitle at the top of Log In and Sign Up.
struct AuthBrandHeader: View {
    let subtitle: String

    var body: some View {
        VStack(spacing: 12) {
            AppMark(size: 56)
            Text("Meeting Memory")
                .font(.title2.bold())
                .foregroundStyle(Palette.ink)
            Text(subtitle)
                .font(.subheadline)
                .foregroundStyle(Palette.secondaryText)
                .multilineTextAlignment(.center)
        }
    }
}

/// Label above a gray rounded input with a leading icon. Secure fields get an eye toggle.
/// `accessory` sits at the trailing end of the label row ("Forgot password?").
struct AuthField<Accessory: View>: View {
    private let label: String
    private let icon: String
    private let placeholder: String
    @Binding private var text: String
    private let isSecure: Bool
    private let contentType: UITextContentType?
    private let keyboard: UIKeyboardType
    private let accessory: Accessory

    @State private var isRevealed = false

    init(
        _ label: String,
        icon: String,
        placeholder: String,
        text: Binding<String>,
        isSecure: Bool = false,
        contentType: UITextContentType? = nil,
        keyboard: UIKeyboardType = .default,
        @ViewBuilder accessory: () -> Accessory
    ) {
        self.label = label
        self.icon = icon
        self.placeholder = placeholder
        _text = text
        self.isSecure = isSecure
        self.contentType = contentType
        self.keyboard = keyboard
        self.accessory = accessory()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(label)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Palette.ink)
                Spacer()
                accessory
            }

            HStack(spacing: 10) {
                Image(systemName: icon)
                    .foregroundStyle(Palette.secondaryText)
                    .frame(width: 18)
                    .accessibilityHidden(true)

                Group {
                    if isSecure && !isRevealed {
                        SecureField(placeholder, text: $text)
                    } else {
                        TextField(placeholder, text: $text)
                    }
                }
                .font(.subheadline)
                .foregroundStyle(Palette.ink)
                .textContentType(contentType)
                .keyboardType(keyboard)
                .textInputAutocapitalization(contentType == .name ? .words : .never)
                .autocorrectionDisabled()

                if isSecure {
                    Button {
                        isRevealed.toggle()
                    } label: {
                        Image(systemName: isRevealed ? "eye.slash" : "eye")
                            .foregroundStyle(Palette.secondaryText)
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(isRevealed ? "Hide password" : "Show password")
                }
            }
            .padding(.horizontal, 14)
            .frame(height: 48)
            .background(RoundedRectangle(cornerRadius: 12, style: .continuous).fill(Palette.fieldFill))
            .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).strokeBorder(Palette.border))
        }
    }
}

extension AuthField where Accessory == EmptyView {
    init(
        _ label: String,
        icon: String,
        placeholder: String,
        text: Binding<String>,
        isSecure: Bool = false,
        contentType: UITextContentType? = nil,
        keyboard: UIKeyboardType = .default
    ) {
        self.init(
            label,
            icon: icon,
            placeholder: placeholder,
            text: text,
            isSecure: isSecure,
            contentType: contentType,
            keyboard: keyboard
        ) {
            EmptyView()
        }
    }
}

/// Divider plus "Don't have an account? Create account" at the bottom of the auth screens.
struct AuthFooter: View {
    let prompt: String
    let actionTitle: String
    let action: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Divider()
            HStack(spacing: 4) {
                Text(prompt)
                    .foregroundStyle(Palette.ink)
                Button(actionTitle, action: action)
                    .fontWeight(.semibold)
                    .foregroundStyle(Palette.brandBlue)
            }
            .font(.footnote)
        }
    }
}
