import SwiftUI

/// The bar strip from MeetingsListView and the audio dock.
/// Bars before `progressIndex` use `activeColor`, the rest use `inactiveColor`.
struct WaveformView: View {
    let peaks: [Double]
    var progressIndex: Int = 0
    var activeColor: Color = .blue
    var inactiveColor: Color = Color(.systemGray3)
    var barWidth: CGFloat = 4

    var body: some View {
        GeometryReader { geo in
            HStack(alignment: .bottom, spacing: 2) {
                ForEach(peaks.indices, id: \.self) { index in
                    Capsule()
                        .fill(index < progressIndex ? activeColor : inactiveColor)
                        .frame(width: barWidth, height: max(1, geo.size.height * peaks[index]))
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
        }
        .opacity(0.6)
    }
}

#Preview {
    WaveformView(peaks: (0..<40).map { _ in Double.random(in: 0.1...0.9) }, progressIndex: 12)
        .frame(height: 20)
        .padding()
}
