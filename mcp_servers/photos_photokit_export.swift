#!/usr/bin/env swift
import Foundation
import AppKit
import Photos
import UniformTypeIdentifiers

struct Manifest: Decodable {
    let photo_ids: [String]?
}

struct Args {
    var manifestPath: String?
    var outputDir: String?
    var resultPath: String?
    var limit: Int = 25
    var dryRun: Bool = true
    var timeoutSeconds: Double = 120
}

var RESULT_JSON_PATH: String?

func parseArgs() -> Args {
    var args = Args()
    var iterator = CommandLine.arguments.dropFirst().makeIterator()
    while let arg = iterator.next() {
        switch arg {
        case "--manifest":
            args.manifestPath = iterator.next()
        case "--output-dir":
            args.outputDir = iterator.next()
        case "--result-json":
            args.resultPath = iterator.next()
        case "--limit":
            args.limit = Int(iterator.next() ?? "") ?? args.limit
        case "--timeout-seconds":
            args.timeoutSeconds = Double(iterator.next() ?? "") ?? args.timeoutSeconds
        case "--apply":
            args.dryRun = false
        case "--dry-run":
            args.dryRun = true
        default:
            continue
        }
    }
    return args
}

func emit(_ payload: [String: Any]) {
    let data = try! JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted, .sortedKeys])
    if let resultPath = RESULT_JSON_PATH {
        try? data.write(to: URL(fileURLWithPath: resultPath), options: .atomic)
    }
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data("\n".utf8))
}

func authorizePhotos() -> PHAuthorizationStatus {
    let current = PHPhotoLibrary.authorizationStatus(for: .readWrite)
    if current != .notDetermined {
        return current
    }
    let sem = DispatchSemaphore(value: 0)
    var resolved = current
    let app = NSApplication.shared
    app.setActivationPolicy(.regular)
    app.activate(ignoringOtherApps: true)
    PHPhotoLibrary.requestAuthorization(for: .readWrite) { status in
        resolved = status
        sem.signal()
    }
    let deadline = Date().addingTimeInterval(120)
    while sem.wait(timeout: .now()) == .timedOut && Date() < deadline {
        RunLoop.current.run(mode: .default, before: Date(timeIntervalSinceNow: 0.1))
    }
    return resolved
}

func preferredExtension(for uti: String?) -> String {
    guard let uti else { return "bin" }
    if #available(macOS 11.0, *) {
        if let type = UTType(uti), let ext = type.preferredFilenameExtension {
            return ext.lowercased()
        }
    }
    let lower = uti.lowercased()
    if lower.contains("heic") { return "heic" }
    if lower.contains("jpeg") || lower.contains("jpg") { return "jpg" }
    if lower.contains("png") { return "png" }
    if lower.contains("tiff") { return "tiff" }
    return "bin"
}

func isoDate(_ date: Date?) -> String? {
    guard let date else { return nil }
    return ISO8601DateFormatter().string(from: date)
}

func uuidPrefix(_ localIdentifier: String) -> String {
    return String(localIdentifier.split(separator: "/").first ?? Substring(localIdentifier))
}

let args = parseArgs()
RESULT_JSON_PATH = args.resultPath
guard let manifestPath = args.manifestPath else {
    emit(["ok": false, "error": "missing --manifest"])
    exit(2)
}

let manifestURL = URL(fileURLWithPath: manifestPath)
let manifestData = try Data(contentsOf: manifestURL)
let manifest = try JSONDecoder().decode(Manifest.self, from: manifestData)
let requestedIDs = Set(manifest.photo_ids ?? [])
if requestedIDs.isEmpty {
    emit(["ok": false, "error": "manifest has no photo_ids"])
    exit(2)
}

let auth = authorizePhotos()
guard auth == .authorized || auth == .limited else {
    emit([
        "ok": false,
        "authorization": "\(auth.rawValue)",
        "error": "photos_access_not_authorized",
        "dry_run": args.dryRun,
        "photos_writes": false,
        "trello_writes": false
    ])
    exit(1)
}

let fetchOptions = PHFetchOptions()
fetchOptions.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: false)]
let fetch = PHAsset.fetchAssets(with: .image, options: fetchOptions)
var matchedAssets: [PHAsset] = []
fetch.enumerateObjects { asset, _, stop in
    let prefix = uuidPrefix(asset.localIdentifier)
    if requestedIDs.contains(prefix) {
        matchedAssets.append(asset)
        if matchedAssets.count >= max(1, args.limit) {
            stop.pointee = true
        }
    }
}

let outputURL = URL(fileURLWithPath: args.outputDir ?? FileManager.default.currentDirectoryPath)
if !args.dryRun {
    try FileManager.default.createDirectory(at: outputURL, withIntermediateDirectories: true)
}

var results: [[String: Any]] = []
for asset in matchedAssets {
    let prefix = uuidPrefix(asset.localIdentifier)
    var item: [String: Any] = [
        "photo_id": prefix,
        "local_identifier": asset.localIdentifier,
        "creation_date": isoDate(asset.creationDate) as Any,
        "width": asset.pixelWidth,
        "height": asset.pixelHeight,
        "dry_run": args.dryRun
    ]
    if args.dryRun {
        item["status"] = "would_export"
        results.append(item)
        continue
    }

    let sem = DispatchSemaphore(value: 0)
    let options = PHImageRequestOptions()
    options.isNetworkAccessAllowed = true
    options.deliveryMode = .highQualityFormat
    options.version = .current
    options.isSynchronous = false
    let requestID = PHImageManager.default().requestImageDataAndOrientation(for: asset, options: options) { data, dataUTI, _, info in
        defer { sem.signal() }
        if let error = info?[PHImageErrorKey] as? Error {
            item["status"] = "error"
            item["error"] = error.localizedDescription
            return
        }
        if (info?[PHImageCancelledKey] as? Bool) == true {
            item["status"] = "cancelled"
            return
        }
        guard let data else {
            item["status"] = "missing_data"
            item["in_cloud"] = info?[PHImageResultIsInCloudKey] as? Bool ?? false
            return
        }
        let ext = preferredExtension(for: dataUTI)
        let target = outputURL.appendingPathComponent("\(prefix).\(ext)")
        do {
            try data.write(to: target, options: .atomic)
            item["status"] = "exported"
            item["exported_path"] = target.path
            item["size"] = data.count
            item["uti"] = dataUTI as Any
        } catch {
            item["status"] = "error"
            item["error"] = error.localizedDescription
        }
    }
    let deadline = Date().addingTimeInterval(args.timeoutSeconds)
    var completed = false
    while Date() < deadline {
        if sem.wait(timeout: .now()) == .success {
            completed = true
            break
        }
        RunLoop.current.run(mode: .default, before: Date(timeIntervalSinceNow: 0.1))
    }
    if !completed {
        PHImageManager.default().cancelImageRequest(requestID)
        item["status"] = "timeout"
    }
    results.append(item)
}

let exported = results.filter { ($0["status"] as? String) == "exported" }.count
emit([
    "ok": true,
    "dry_run": args.dryRun,
    "authorization": "\(auth.rawValue)",
    "requested_photo_ids": requestedIDs.count,
    "matched_assets": matchedAssets.count,
    "exported": exported,
    "limit": args.limit,
    "output_dir": outputURL.path,
    "results": results,
    "safety": [
        "photos_writes": false,
        "local_file_writes": !args.dryRun,
        "trello_writes": false,
        "icloud_network_access_allowed": !args.dryRun
    ]
])
