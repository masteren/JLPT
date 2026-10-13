// 把 PDF 的指定页渲染成 PNG（macOS 版，和 render_pdf.ps1 对应）。
//
// 用法:
//   swift 工具/render_pdf.swift "题/.../某.pdf" <输出目录> [页码，如 1,2,3；省略则全部] [宽度，默认 1700]
//
// 走系统自带的 PDFKit，不需要装 poppler / ImageMagick。
// 输出到 <输出目录>/page-001.png，目录不存在会自动创建。
import AppKit
import PDFKit

let args = CommandLine.arguments
guard args.count >= 3 else {
    FileHandle.standardError.write("用法: swift 工具/render_pdf.swift <pdf> <输出目录> [页码] [宽度]\n".data(using: .utf8)!)
    exit(1)
}
guard let doc = PDFDocument(url: URL(fileURLWithPath: args[1])) else {
    FileHandle.standardError.write("打不开 PDF: \(args[1])\n".data(using: .utf8)!)
    exit(1)
}
let outDir = URL(fileURLWithPath: args[2])
try FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)
let pages = args.count > 3 && !args[3].isEmpty
    ? args[3].split(separator: ",").compactMap { Int($0.trimmingCharacters(in: .whitespaces)) }
    : Array(1...doc.pageCount)
let width = args.count > 4 ? CGFloat(Double(args[4]) ?? 1700) : 1700
print("pagecount=\(doc.pageCount)")

for p in pages {
    guard let page = doc.page(at: p - 1) else { print("跳过第 \(p) 页（超出范围）"); continue }
    let box = page.bounds(for: .mediaBox)
    let size = NSSize(width: width, height: box.height * width / box.width)
    let img = page.thumbnail(of: size, for: .mediaBox)
    guard let tiff = img.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff),
          let png = rep.representation(using: .png, properties: [:]) else { continue }
    let out = outDir.appendingPathComponent(String(format: "page-%03d.png", p))
    try png.write(to: out)
    print(out.path)
}
