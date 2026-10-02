import Supabase

/// The app's one Supabase client. Only its Auth part is used: all data goes
/// through the FastAPI backend (spec D5). Sessions are kept in the Keychain.
enum SupabaseService {
    static let client = SupabaseClient(
        supabaseURL: LabSyncConfig.supabaseURL,
        supabaseKey: LabSyncConfig.supabaseAnonKey
    )
}
