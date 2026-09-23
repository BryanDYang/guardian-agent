import SwiftUI

/// The colored initials circle (w-10 h-10 rounded-full, etc. in the TS).
struct AvatarView: View {
    let initials: String
    let colorHex: String
    var size: CGFloat = 40
    /// Matches the `grayscale` class on completed task rows.
    var isMuted: Bool = false

    var body: some View {
        Text(initials)
            .font(.system(size: size * 0.35, weight: .semibold))
            .foregroundStyle(.white)
            .frame(width: size, height: size)
            .background(Circle().fill(Color(hex: colorHex)))
            .grayscale(isMuted ? 1 : 0)
    }
}

#Preview {
    HStack(spacing: 12) {
        AvatarView(initials: "AC", colorHex: "#3B82F6", size: 24)
        AvatarView(initials: "BS", colorHex: "#22C55E")
        AvatarView(initials: "CD", colorHex: "#F59E0B", size: 56)
        AvatarView(initials: "CD", colorHex: "#F59E0B", isMuted: true)
    }
    .padding()
}
