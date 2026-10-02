import Foundation

/// Settings from LabSyncConfig.plist (gitignored; start from LabSyncConfig.example.plist).
enum LabSyncConfig {
    private static let values: [String: String] = Bundle.main
        .url(forResource: "LabSyncConfig", withExtension: "plist")
        .flatMap { NSDictionary(contentsOf: $0) as? [String: String] } ?? [:]

    static let baseURL = values["BaseURL"].flatMap(URL.init(string:))
        ?? URL(string: "http://127.0.0.1:8000")!

    static var supabaseURL: URL {
        guard let url = values["SupabaseURL"].flatMap(URL.init(string:)) else {
            fatalError("Set SupabaseURL in LabSyncConfig.plist")
        }
        return url
    }

    static var supabaseAnonKey: String {
        guard let key = values["SupabaseAnonKey"], !key.isEmpty else {
            fatalError("Set SupabaseAnonKey in LabSyncConfig.plist")
        }
        return key
    }
}
