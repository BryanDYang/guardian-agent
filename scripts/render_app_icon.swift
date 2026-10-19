// Editable geometric source for the app icon and in-app mark.
// Run from the repository root: swift scripts/render_app_icon.swift
import AppKit

let assets = URL(fileURLWithPath: "ios/MeetingApp/MeetingApp/Assets.xcassets")
func color(_ hex: UInt32) -> CGColor {
    CGColor(red: CGFloat((hex >> 16) & 255) / 255,
            green: CGFloat((hex >> 8) & 255) / 255,
            blue: CGFloat(hex & 255) / 255, alpha: 1)
}

// All coordinates use a 1024-point canvas with an origin at the top left.
let bubble = CGMutablePath()
bubble.move(to: CGPoint(x: 322, y: 270))
bubble.addLine(to: CGPoint(x: 702, y: 270))
bubble.addCurve(to: CGPoint(x: 790, y: 358), control1: CGPoint(x: 751, y: 270), control2: CGPoint(x: 790, y: 309))
bubble.addLine(to: CGPoint(x: 790, y: 618))
bubble.addCurve(to: CGPoint(x: 702, y: 706), control1: CGPoint(x: 790, y: 667), control2: CGPoint(x: 751, y: 706))
bubble.addLine(to: CGPoint(x: 416, y: 706))
bubble.addLine(to: CGPoint(x: 290, y: 788))
bubble.addLine(to: CGPoint(x: 290, y: 700))
bubble.addCurve(to: CGPoint(x: 234, y: 618), control1: CGPoint(x: 254, y: 688), control2: CGPoint(x: 234, y: 657))
bubble.addLine(to: CGPoint(x: 234, y: 358))
bubble.addCurve(to: CGPoint(x: 322, y: 270), control1: CGPoint(x: 234, y: 309), control2: CGPoint(x: 273, y: 270))
bubble.closeSubpath()
let check = CGMutablePath()
check.move(to: CGPoint(x: 392, y: 490))
check.addLine(to: CGPoint(x: 478, y: 576))
check.addLine(to: CGPoint(x: 638, y: 412))

for (name, background) in [("Light", UInt32(0x173F49)), ("Dark", UInt32(0x102B33))] {
    let canvas = CGContext(data: nil, width: 1024, height: 1024, bitsPerComponent: 8,
                           bytesPerRow: 4096, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                           bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    canvas.translateBy(x: 0, y: 1024)
    canvas.scaleBy(x: 1, y: -1)
    canvas.setFillColor(color(background))
    canvas.fill(CGRect(x: 0, y: 0, width: 1024, height: 1024))
    canvas.setFillColor(color(0xF6F4EC))
    canvas.addPath(bubble)
    canvas.fillPath()
    canvas.setStrokeColor(color(background))
    canvas.setLineWidth(58)
    canvas.setLineCap(.round)
    canvas.setLineJoin(.round)
    canvas.addPath(check)
    canvas.strokePath()
    let png = NSBitmapImageRep(cgImage: canvas.makeImage()!).representation(using: .png, properties: [:])!
    try png.write(to: assets.appendingPathComponent("AppIcon.appiconset/AppIcon-\(name).png"))
    try png.write(to: assets.appendingPathComponent("BrandMark.imageset/BrandMark-\(name).png"))
}
