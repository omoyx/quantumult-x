"""Validate only this public profile and its public upstreams; stdlib only.

Domain probes model sequential matching with inserted resources before local rules.
They do not implement QX DNS, request optimization, ASN lookup or HTTPS inspection.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from test_profile import PROFILE, fields, options, read_sections, validate_probe_url
from routing import CUSTOM_URL, ordered_rules, parse_rules, route

ROOT = Path(__file__).resolve().parent
SIRI = "https://raw.githubusercontent.com/byx020119/Shadowrocket-Siri/main/siri3.list"
PARSER = "https://raw.githubusercontent.com/KOP-XIAO/QuantumultX/master/Scripts/resource-parser.js"
ICON_PREFIXES = (
    "https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/",
    "https://raw.githubusercontent.com/lige47/lige_icon/e28d76ff1fe63c693949f6937545ccbc86ca3c22/icon/",
)
# Expected policy names, not claims about unlock or actual egress.
PROBES = {
    "guzzoni.apple.com": "AI", "seed.siri.apple.com": "AI",
    "apple-relay.cloudflare.com": "AI", "gateway.icloud.com": "direct",
    "mask.icloud.com": "AI", "metrics.icloud.com": "AI",
    "chatgpt.com": "AI服务", "api.openai.com": "AI服务",
    "claude.ai": "AI服务", "api.anthropic.com": "AI服务",
    "gemini.google.com": "AI服务", "aistudio.google.com": "AI服务",
    "notebooklm.google.com": "AI服务", "notebooklm.google": "AI服务",
    "copilot.microsoft.com": "AI服务", "api.perplexity.ai": "AI服务",
    "www.netflix.com": "Netflix", "www.disneyplus.com": "Disney+",
    "www.youtube.com": "YouTube", "i.ytimg.com": "YouTube",
    "open.spotify.com": "Spotify", "ani.gamer.com.tw": "巴哈姆特",
    "api.telegram.org": "Telegram", "www.twitch.tv": "流媒体",
    "www.apple.com": "Apple", "apps.apple.com": "Apple",
    "www.google.com": "Google", "www.microsoft.com": "Microsoft",
    "www.baidu.com": "direct", "www.bilibili.com": "direct",
    "www.qq.com": "direct", "router.local": "direct",
    "routing-probe.invalid": "兜底",
    "iosapps.itunes.apple.com": "direct", "iosapps-ssl.itunes.apple.com": "direct",
    "ussea3.icloud-content.com": "direct", "edge-297.hkhkg2.icloud-content.com": "direct",
    "edge-291.hkhkg2.icloud-content.com": "direct", "cvws.icloud-content.com": "direct",
    "routing-probe.icloud-content.com.cn": "direct",
    "gcs-us-00003.content-storage-upload.googleapis.com": "direct",
    "gcs-eu-00002.content-storage-upload.googleapis.com": "direct",
    "googleapis.com": "Google", "storage.googleapis.com": "Google",
}


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "QX-Public-Profile-Check/1"}), timeout=30) as response:
        content = response.read()
        if response.status != 200 or response.url != url:
            raise ValueError(f"Unexpected response/redirect for {url}")
        return content, {"url": url, "resolved_url": response.url,
                         "status": response.status, "bytes": len(content),
                         "sha256": hashlib.sha256(content).hexdigest()}


def check_parser(parser, siri, expected):
    if not shutil.which("node"):
        raise RuntimeError("node is required for the public parser integration check")
    result = subprocess.run(["node", str(ROOT / "check_parser.cjs")],
                            input=json.dumps({"parser": parser, "siri": siri}),
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Public parser integration check failed:\n" + result.stderr)
    parsed = json.loads(result.stdout)
    actual = [(p[0].lower(), p[1], "AI") for p in map(fields, parsed["siri"].splitlines())]
    if actual != expected:
        raise ValueError("KOP Siri conversion differs from the expected QX rules")
    return {"siri_rules": len(actual), "fictional_ss_nodes": parsed["nodes"],
            "fictional_jms_renamed_tags": parsed["renamed_jms_tags"],
            "fictional_jms_explicit_flag_tags": parsed["explicit_flag_tags"],
            "fictional_jms_compact_tags": parsed["compact_jms_tags"],
            "compact_connection_fields_unchanged": parsed["compact_connection_fields_unchanged"],
            "fictional_jms_download_tags": parsed["download_jms_tags"],
            "download_connection_fields_unchanged": parsed["download_connection_fields_unchanged"]}


def online_check(published=False):
    sections = read_sections()
    resources = []
    for line in sections["filter_remote"]:
        url, *parts = fields(line)
        if url.startswith("https://"):
            resources.append((url, options(parts)))
    icons = []
    for line in sections["policy"]:
        name, *parts = fields(line.partition("=")[2])
        url = options(parts).get("img-url")
        if not url or not url.startswith(ICON_PREFIXES):
            raise ValueError(f"Missing or unexpected policy icon for {name}")
        icons.append((name, url))
    urls = list(dict.fromkeys([PARSER, SIRI] + [url for url, _ in resources if url != CUSTOM_URL]
                             + [url for _, url in icons]))
    if published:
        urls.extend([CUSTOM_URL, CUSTOM_URL.replace("Custom.list", "Custom-compat.list")])
    with ThreadPoolExecutor(max_workers=6) as pool:
        fetched = dict(zip(urls, pool.map(fetch, urls)))
    receipt = {"verified_at": datetime.now(timezone.utc).isoformat(),
               "scope": "Public files and domain routing model; no QX import, user subscription, node or unlock test.",
               "profile_sha256": hashlib.sha256(PROFILE.read_bytes()).hexdigest(),
               "sources": [], "policy_icons": [], "domain_probes": []}
    for name, url in icons:
        content, source = fetched[url]
        if not content.startswith(b"\x89PNG\r\n\x1a\n") or content[12:16] != b"IHDR":
            raise ValueError(f"Policy icon is not a PNG: {name}")
        width, height = struct.unpack(">II", content[16:24])
        if width != height or not 32 <= width <= 2048:
            raise ValueError(f"Unexpected policy icon dimensions: {name}")
        receipt["policy_icons"].append(dict(source, policy=name, width=width, height=height))
    siri_rules = parse_rules(fetched[SIRI][0].decode("utf-8-sig"), siri=True)
    snapshot = [", ".join(rule) for rule in siri_rules]
    siri_source = dict(fetched[SIRI][1], rule_count=len(siri_rules),
                       native_snapshot=snapshot, role="reviewed compatibility upstream")
    receipt["sources"].append(fetched[PARSER][1])
    receipt["sources"].append(siri_source)
    receipt["managed_rules"] = []
    for filename in ("Custom.list", "Custom-compat.list"):
        content = (ROOT / "rules" / filename).read_bytes()
        source = {"path": "rules/" + filename, "bytes": len(content),
                  "sha256": hashlib.sha256(content).hexdigest(), "origin": "working-tree"}
        if published:
            url = CUSTOM_URL.replace("Custom.list", filename)
            if fetched[url][0] != content:
                raise ValueError(f"Published managed rules differ: {filename}")
            source.update(fetched[url][1], origin="published-and-compared")
        receipt["managed_rules"].append(source)
    custom = parse_rules((ROOT / "rules/Custom.list").read_text())
    for kind, value, policy in siri_rules:
        expected = (kind, value, "direct" if value == "gateway.icloud.com" else policy)
        if expected not in custom:
            raise ValueError(f"Upstream Siri changed: review managed rules for {value}")
    expected_keys = {(kind, value) for kind, value, _ in siri_rules}
    actual_keys = {(kind, value) for kind, value, policy in custom if policy == "AI"}
    actual_keys.add(("host", "gateway.icloud.com"))
    if actual_keys != expected_keys:
        raise ValueError("Upstream Siri removed or changed a rule: review managed rules")
    remote_rules = {CUSTOM_URL: custom}
    for url, opts in resources:
        if url == CUSTOM_URL:
            continue
        content, source = fetched[url]
        rules = parse_rules(content.decode("utf-8-sig"))
        source.update(rule_count=len(rules), types=sorted({r[0] for r in rules}))
        receipt["sources"].append(source)
        remote_rules[url] = rules
    ordered, fallback = ordered_rules(sections, remote_rules)
    for domain, expected in PROBES.items():
        actual = route(domain, ordered, fallback)
        receipt["domain_probes"].append({"domain": domain, "expected": expected, "actual": actual})
        if actual != expected:
            raise ValueError(f"Routing regression for {domain}: expected {expected}, got {actual}")
    receipt["parser_check"] = check_parser(fetched[PARSER][0].decode(), fetched[SIRI][0].decode(), siri_rules)
    general = {key.strip(): value.strip() for key, value in options(sections["general"]).items()}
    endpoint = validate_probe_url(general["server_check_url"])
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    with build_opener(NoRedirect).open(Request(endpoint, method="HEAD"), timeout=30) as response:
        if response.status != 204 or response.url != endpoint:
            raise ValueError("Latency endpoint no longer returns 204 without redirect")
        receipt["benchmark"] = {"url": endpoint, "method": "HEAD", "status": response.status,
                                "scope": "Current host connection only; no user nodes tested"}
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="Fetch public upstreams and test domain routing")
    parser.add_argument("--published", action="store_true", help="Also compare published managed rules to local files")
    parser.add_argument("--report", type=Path, help="Write public validation evidence as JSON")
    args = parser.parse_args()
    subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(ROOT),
                    "-p", "test_profile.py", "-v"], check=True)
    if args.online:
        receipt = online_check(published=args.published)
        if args.report:
            args.report.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        print(f"PASS: {len(receipt['sources'])} public sources; {len(receipt['policy_icons'])} policy PNGs; "
              f"{len(PROBES)} domain probes; KOP parser; HEAD 204")
    elif args.report or args.published:
        parser.error("--report and --published require --online")


if __name__ == "__main__":
    main()
