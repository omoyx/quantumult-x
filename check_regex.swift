// Check the public profile using Foundation's ICU-backed regular expressions.
import Foundation

let config = try String(contentsOfFile: CommandLine.arguments[1], encoding: .utf8)
var patterns: [String: NSRegularExpression] = [:]
for raw in config.components(separatedBy: .newlines) {
    let line = raw.trimmingCharacters(in: .whitespaces)
    guard !line.hasPrefix("#"), let range = line.range(of: "server-tag-regex=") else { continue }
    let name = line.components(separatedBy: "=")[1].components(separatedBy: ",")[0].trimmingCharacters(in: .whitespaces)
    let pattern = String(line[range.upperBound...]).components(separatedBy: ",")[0]
    patterns[name] = try NSRegularExpression(pattern: pattern)
}
let input = FileHandle.standardInput.readDataToEndOfFile()
let cases = try JSONSerialization.jsonObject(with: input) as! [[String: Any]]
for sample in cases {
    let name = sample["name"] as! String
    let expected = (sample["groups"] as! [String]).sorted()
    let actual = patterns.compactMap { key, regex in
        regex.firstMatch(in: name, range: NSRange(name.startIndex..., in: name)) == nil ? nil : key
    }.sorted()
    guard actual == expected else {
        fputs("ICU mismatch: \(name): \(actual) != \(expected)\n", stderr)
        exit(1)
    }
}
print("PASS: \(patterns.count) ICU expressions; \(cases.count) node labels")
