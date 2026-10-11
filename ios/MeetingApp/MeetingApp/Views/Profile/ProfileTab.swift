import SwiftData
import SwiftUI

/// Fourth tab: who you are, your task counts, settings, and Sign Out.
///
/// Visual language: adaptive canvas and grouped surfaces, monochrome icons,
/// one accent color (brand blue). Red appears only where it carries meaning:
/// overdue tasks and Sign Out.
struct ProfileTab: View {
    @Environment(AppSession.self) private var session
    @Environment(MeetingNavigator.self) private var navigator
    @State private var showingEditProfile = false
    @Query private var projects: [Project]
    @State private var tasks = RemoteTaskSummary(open: 0, overdue: 0, done: 0)

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 32) {
                    identity
                    taskSummary
                    accountSection
                    appSection
                    signOutButton
                }
                .padding(.horizontal, 20)
                .padding(.top, 32)
                .padding(.bottom, 24)
            }
            .background(Color(uiColor: .systemBackground))
            .toolbar(.hidden, for: .navigationBar)
            .sheet(isPresented: $showingEditProfile) {
                EditProfileSheet()
            }
            .task { await refresh() }
        }
    }

    private func refresh() async {
        await session.refreshProfile()
        if let summary = try? await MeetingAPIClient.shared.taskSummary() {
            tasks = summary
        }
    }

    // MARK: - Identity

    private var identity: some View {
        VStack(spacing: 14) {
            Text(session.user.initial)
                .font(.system(size: 30, weight: .semibold))
                .foregroundStyle(.white)
                .frame(width: 80, height: 80)
                .background(
                    Circle().fill(
                        LinearGradient(
                            colors: [Palette.brandIndigo, Palette.brandBlue],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                )
                .accessibilityHidden(true)

            VStack(spacing: 4) {
                Text(session.user.name)
                    .font(.title2.bold())
                    .foregroundStyle(ProfileStyle.text)
                if !session.user.title.isEmpty {
                    Text(session.user.title)
                        .font(.subheadline)
                        .foregroundStyle(ProfileStyle.text.opacity(0.75))
                }
                Text(session.user.email)
                    .font(.subheadline)
                    .foregroundStyle(ProfileStyle.secondaryText)
            }
            .multilineTextAlignment(.center)

            Button("Edit profile") { showingEditProfile = true }
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(ProfileStyle.text)
                .padding(.horizontal, 18)
                .padding(.vertical, 8)
                .background(Capsule().fill(ProfileStyle.surface))
                .buttonStyle(.plain)
        }
        .frame(maxWidth: .infinity)
    }

    // MARK: - Tasks

    private var taskSummary: some View {
        VStack(alignment: .leading, spacing: 10) {
            SectionHeader("My tasks")

            Button {
                navigator.activeTab = .tasks
            } label: {
                HStack(spacing: 0) {
                    TaskStat(value: tasks.open, label: "Open")
                    TaskStat(value: tasks.overdue, label: "Overdue", isAlert: tasks.overdue > 0)
                    TaskStat(value: tasks.done, label: "Done")
                }
                .padding(.vertical, 18)
            }
            .buttonStyle(RowButtonStyle())
            .clipShape(RoundedRectangle(cornerRadius: ProfileStyle.cornerRadius, style: .continuous))
            .accessibilityHint("Opens the Tasks tab")
        }
    }

    // MARK: - Settings

    private var accountSection: some View {
        let pending = session.pendingInvitationCount
        let active = projects.filter { isServerID($0.id) }.count

        return MenuSection("Account") {
            NavigationLink {
                WorkspacesView()
            } label: {
                ProfileMenuRow(
                    symbol: "square.stack",
                    title: "Workspaces",
                    detail: pending > 0
                        ? .badge("\(pending) \(pending == 1 ? "invite" : "invites")")
                        : .text("\(active)")
                )
            }
            RowDivider()

            NavigationLink {
                SpeakerIdentityView()
            } label: {
                ProfileMenuRow(
                    symbol: "waveform",
                    title: "Voice recognition",
                    detail: session.user.hasVoiceprint ? .text("On") : .action("Set up")
                )
            }
            RowDivider()

            NavigationLink {
                SecurityCredentialsView()
            } label: {
                ProfileMenuRow(
                    symbol: "lock",
                    title: "Sign-in & security",
                    detail: .text(signInSummary)
                )
            }
        }
    }

    private var appSection: some View {
        MenuSection("App") {
            NavigationLink {
                NotificationsIntegrationsView()
            } label: {
                ProfileMenuRow(symbol: "bell", title: "Notifications")
            }
            RowDivider()

            NavigationLink {
                PrivacyDataView()
            } label: {
                ProfileMenuRow(symbol: "hand.raised", title: "Privacy & data")
            }
            RowDivider()

            NavigationLink {
                AboutView()
            } label: {
                ProfileMenuRow(
                    symbol: "info.circle",
                    title: "About",
                    detail: .text("v\(ProfilePlaceholder.appVersion)")
                )
            }
        }
    }

    private var signInSummary: String {
        let methods = session.user.signInMethods
        switch (methods.contains(.email), methods.contains(.google)) {
        case (true, true): return "Email, Google"
        case (false, true): return "Google"
        default: return "Email"
        }
    }

    // MARK: - Sign out

    private var signOutButton: some View {
        Button {
            Task { await session.signOut() }
        } label: {
            Text("Sign Out")
                .font(.body.weight(.medium))
                .foregroundStyle(Palette.danger)
                .frame(maxWidth: .infinity, minHeight: 52)
        }
        .buttonStyle(RowButtonStyle())
        .clipShape(RoundedRectangle(cornerRadius: ProfileStyle.cornerRadius, style: .continuous))
    }
}

// MARK: - Pieces

private enum ProfileStyle {
    static let text = Color(uiColor: .label)
    static let secondaryText = Color(uiColor: .secondaryLabel)
    static let surface = Color(uiColor: .secondarySystemBackground)
    static let pressed = Color(uiColor: .tertiarySystemFill)
    static let hairline = Color(uiColor: .separator)
    static let chevron = Color(uiColor: .tertiaryLabel)
    static let cornerRadius: CGFloat = 18
}

private struct SectionHeader: View {
    let title: String

    init(_ title: String) {
        self.title = title
    }

    var body: some View {
        Text(title.uppercased())
            .font(.caption.weight(.semibold))
            .tracking(1.2)
            .foregroundStyle(ProfileStyle.secondaryText)
            .padding(.leading, 4)
            .accessibilityAddTraits(.isHeader)
    }
}

/// A titled group of rows on a soft gray surface.
private struct MenuSection<Rows: View>: View {
    let title: String
    let rows: Rows

    init(_ title: String, @ViewBuilder rows: () -> Rows) {
        self.title = title
        self.rows = rows()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            SectionHeader(title)
            VStack(spacing: 0) { rows }
                .buttonStyle(RowButtonStyle())
                .clipShape(RoundedRectangle(cornerRadius: ProfileStyle.cornerRadius, style: .continuous))
        }
    }
}

/// Inset so the line starts under the title, not under the icon.
private struct RowDivider: View {
    var body: some View {
        Rectangle()
            .fill(ProfileStyle.hairline)
            .frame(height: 1)
            .padding(.leading, 54)
            .background(ProfileStyle.surface)
    }
}

private struct TaskStat: View {
    let value: Int
    let label: String
    var isAlert = false

    var body: some View {
        VStack(spacing: 4) {
            Text("\(value)")
                .font(.system(.title2, design: .rounded, weight: .semibold))
                .monospacedDigit()
                .foregroundStyle(isAlert ? Palette.danger : ProfileStyle.text)
            Text(label)
                .font(.caption)
                .foregroundStyle(ProfileStyle.secondaryText)
        }
        .frame(maxWidth: .infinity)
        .accessibilityElement(children: .combine)
    }
}

private struct ProfileMenuRow: View {
    /// What sits before the chevron: a quiet value, a blue call to action, or a count badge.
    enum Detail {
        case none
        case text(String)
        case action(String)
        case badge(String)
    }

    let symbol: String
    let title: String
    var detail: Detail = .none

    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: symbol)
                .font(.system(size: 17))
                .foregroundStyle(ProfileStyle.text.opacity(0.6))
                .frame(width: 24)
                .accessibilityHidden(true)

            Text(title)
                .font(.body)
                .foregroundStyle(ProfileStyle.text)

            Spacer(minLength: 8)

            detailView
                .lineLimit(1)

            Image(systemName: "chevron.right")
                .font(.footnote.weight(.semibold))
                .foregroundStyle(ProfileStyle.chevron)
                .accessibilityHidden(true)
        }
        .padding(.horizontal, 16)
        .frame(minHeight: 52)
        .contentShape(Rectangle())
    }

    @ViewBuilder
    private var detailView: some View {
        switch detail {
        case .none:
            EmptyView()
        case .text(let value):
            Text(value)
                .font(.subheadline)
                .foregroundStyle(ProfileStyle.secondaryText)
        case .action(let value):
            Text(value)
                .font(.subheadline.weight(.medium))
                .foregroundStyle(Palette.brandBlue)
        case .badge(let value):
            Text(value)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.white)
                .padding(.horizontal, 8)
                .padding(.vertical, 3)
                .background(Capsule().fill(Palette.brandBlue))
        }
    }
}

/// Soft gray row that darkens slightly while pressed, like a native grouped list.
private struct RowButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .background(configuration.isPressed ? ProfileStyle.pressed : ProfileStyle.surface)
    }
}

#Preview {
    ProfileTab()
        .environment(AppSession(stage: .signedIn, user: PlaceholderUser(name: "Will Liu", email: "will@example.com")))
        .environment(MeetingNavigator())
        .modelContainer(PreviewContainer.shared)
}