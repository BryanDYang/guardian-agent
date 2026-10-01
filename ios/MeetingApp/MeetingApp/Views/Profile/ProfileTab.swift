import SwiftUI

/// Fourth tab: identity header with task stats, settings menu, and Sign Out.
///
/// Visual language: neutral surfaces, monochrome icons, one accent color (brand blue).
/// Red appears only where it carries meaning: overdue tasks and Sign Out.
struct ProfileTab: View {
    @Environment(AppSession.self) private var session
    @Environment(MeetingNavigator.self) private var navigator
    @State private var showingEditProfile = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    headerCard
                    menuCard
                    signOutButton
                }
                .padding(16)
            }
            .background(Palette.screenBackground)
            .toolbar(.hidden, for: .navigationBar)
            .sheet(isPresented: $showingEditProfile) {
                EditProfileSheet()
            }
        }
    }

    // MARK: - Header

    private var headerCard: some View {
        VStack(spacing: 18) {
            HStack(spacing: 14) {
                Text(session.user.initial)
                    .font(.title2.weight(.semibold))
                    .foregroundStyle(.white)
                    .frame(width: 56, height: 56)
                    .background(Circle().fill(Palette.brandBlue))
                    .accessibilityHidden(true)

                VStack(alignment: .leading, spacing: 2) {
                    Text(session.user.name)
                        .font(.headline)
                        .foregroundStyle(Palette.ink)
                    Text(session.user.email)
                        .font(.subheadline)
                        .foregroundStyle(Palette.secondaryText)
                    Button("Edit Profile") { showingEditProfile = true }
                        .font(.footnote.weight(.semibold))
                        .foregroundStyle(Palette.brandBlue)
                        .padding(.top, 6)
                }

                Spacer()

                // Placeholder: the mockup shows this icon button but not what it opens.
                Button {} label: {
                    Image(systemName: "ellipsis")
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(Palette.secondaryText)
                        .frame(width: 32, height: 32)
                        .background(Circle().fill(ProfileStyle.tileFill))
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Profile options")
            }

            Rectangle()
                .fill(ProfileStyle.hairline)
                .frame(height: 1)

            Button {
                navigator.activeTab = .tasks
            } label: {
                HStack(spacing: 0) {
                    TaskStat(value: ProfilePlaceholder.openTasks, label: "Open")
                    statDivider
                    TaskStat(
                        value: ProfilePlaceholder.overdueTasks,
                        label: "Overdue",
                        isAlert: ProfilePlaceholder.overdueTasks > 0
                    )
                    statDivider
                    TaskStat(value: ProfilePlaceholder.doneTasks, label: "Done")
                }
            }
            .buttonStyle(.plain)
            .accessibilityHint("Opens the Tasks tab")
        }
        .padding(20)
        .profileCard()
    }

    private var statDivider: some View {
        Rectangle()
            .fill(ProfileStyle.hairline)
            .frame(width: 1, height: 28)
    }

    // MARK: - Menu

    private var menuCard: some View {
        let pending = ProfilePlaceholder.invitations.count
        let active = ProfilePlaceholder.workspaces.count

        return VStack(spacing: 0) {
            NavigationLink {
                WorkspacesView()
            } label: {
                ProfileMenuRow(
                    symbol: "building.2",
                    title: "Workspaces",
                    subtitle: "\(active) active \u{2022} \(pending) pending \(pending == 1 ? "invite" : "invites")",
                    showsBadge: pending > 0
                )
            }
            rowDivider

            NavigationLink {
                SpeakerIdentityView()
            } label: {
                ProfileMenuRow(
                    symbol: "person.wave.2",
                    title: "Speaker Identity & Diarization",
                    subtitle: session.user.hasVoiceprint
                        ? "Voiceprint enrolled \u{2022} Attendee mapping"
                        : "Not enrolled \u{2022} Record your voice"
                )
            }
            rowDivider

            NavigationLink {
                NotificationsIntegrationsView()
            } label: {
                ProfileMenuRow(
                    symbol: "bell",
                    title: "Notifications & Integrations",
                    subtitle: "Apple Reminders, Calendar & Push Alerts"
                )
            }
            rowDivider

            NavigationLink {
                PrivacyDataView()
            } label: {
                ProfileMenuRow(
                    symbol: "hand.raised",
                    title: "Privacy & Data Management",
                    subtitle: "Export data & account wipe"
                )
            }
            rowDivider

            NavigationLink {
                SecurityCredentialsView()
            } label: {
                ProfileMenuRow(
                    symbol: "key",
                    title: "Security & Credentials",
                    subtitle: "Password & Google authentication"
                )
            }
            rowDivider

            NavigationLink {
                AboutView()
            } label: {
                ProfileMenuRow(
                    symbol: "info.circle",
                    title: "About Meeting Memory",
                    subtitle: "v\(ProfilePlaceholder.appVersion) \u{2022} Terms, Privacy & Support"
                )
            }
        }
        .buttonStyle(RowButtonStyle())
        .clipShape(RoundedRectangle(cornerRadius: ProfileStyle.cornerRadius, style: .continuous))
        .profileCard()
    }

    /// Inset so the line starts under the text, not under the icon.
    private var rowDivider: some View {
        Rectangle()
            .fill(ProfileStyle.hairline)
            .frame(height: 1)
            .padding(.leading, 62)
    }

    // MARK: - Sign out

    private var signOutButton: some View {
        Button(action: session.signOut) {
            Text("Sign Out")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(Palette.danger)
                .frame(maxWidth: .infinity, minHeight: 50)
        }
        .buttonStyle(RowButtonStyle())
        .clipShape(RoundedRectangle(cornerRadius: ProfileStyle.cornerRadius, style: .continuous))
        .profileCard()
    }
}

// MARK: - Pieces

private enum ProfileStyle {
    static let tileFill = Color(hex: "#F2F4F7")
    static let hairline = Color(hex: "#E8EBF0")
    static let chevron = Color(hex: "#C4CAD4")
    static let cornerRadius: CGFloat = 16
}

private struct TaskStat: View {
    let value: Int
    let label: String
    var isAlert = false

    var body: some View {
        VStack(spacing: 2) {
            Text("\(value)")
                .font(.title3.weight(.semibold))
                .monospacedDigit()
                .foregroundStyle(isAlert ? Palette.danger : Palette.ink)
            Text(label)
                .font(.caption)
                .foregroundStyle(Palette.secondaryText)
        }
        .frame(maxWidth: .infinity)
        .accessibilityElement(children: .combine)
    }
}

private struct ProfileMenuRow: View {
    let symbol: String
    let title: String
    let subtitle: String
    var showsBadge = false

    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: symbol)
                .font(.system(size: 15))
                .foregroundStyle(Palette.ink.opacity(0.7))
                .frame(width: 32, height: 32)
                .background(
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .fill(ProfileStyle.tileFill)
                )
                .accessibilityHidden(true)

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(Palette.ink)
                Text(subtitle)
                    .font(.caption)
                    .foregroundStyle(Palette.secondaryText)
                    .lineLimit(1)
            }

            Spacer(minLength: 8)

            if showsBadge {
                Circle()
                    .fill(Palette.brandBlue)
                    .frame(width: 6, height: 6)
                    .accessibilityLabel("Pending invitation")
            }

            Image(systemName: "chevron.right")
                .font(.caption.weight(.semibold))
                .foregroundStyle(ProfileStyle.chevron)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 13)
        .contentShape(Rectangle())
    }
}

/// White row that tints gray while pressed, like a native grouped list.
private struct RowButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .background(configuration.isPressed ? ProfileStyle.tileFill : Color.white)
    }
}

private extension View {
    func profileCard() -> some View {
        background(
            RoundedRectangle(cornerRadius: ProfileStyle.cornerRadius, style: .continuous)
                .fill(.white)
        )
        .overlay(
            RoundedRectangle(cornerRadius: ProfileStyle.cornerRadius, style: .continuous)
                .strokeBorder(ProfileStyle.hairline)
        )
    }
}

#Preview {
    ProfileTab()
        .environment(AppSession(stage: .signedIn, user: PlaceholderUser(name: "a", email: "a@a.com")))
        .environment(MeetingNavigator())
}