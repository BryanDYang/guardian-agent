import SwiftUI
import SwiftData

// App.tsx → bottom tab bar
struct RootTabView: View {
    @Environment(MeetingNavigator.self) private var navigator

    var body: some View {
        @Bindable var navigator = navigator

        TabView(selection: $navigator.activeTab) {
            MeetingsTab()
                .tabItem { Label("Meetings", systemImage: "mic") }
                .tag(Tab.meetings)

            TasksView()
                .tabItem { Label("Tasks", systemImage: "checkmark.square") }
                .tag(Tab.tasks)

            ChatView()
                .tabItem { Label("Chat", systemImage: "message") }
                .tag(Tab.chat)
        }
    }
}

#Preview {
    RootTabView()
        .environment(MeetingNavigator())
        .modelContainer(PreviewContainer.shared)
}
