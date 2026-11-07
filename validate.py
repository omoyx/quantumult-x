"""Validate only this public profile and its public upstreams; stdlib only.

Domain probes model sequential, local-first matching with the final rule last.
They do not implement QX DNS, request optimization, ASN lookup or HTTPS inspection.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import fnmatch
import hashlib
import ipaddress
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.request import Request, urlopen

from test_profile import PROFILE, fields, options, read_sections

ROOT = Path(__file__).resolve().parent
SIRI = "https://raw.githubusercontent.com/byx020119/Shadowrocket-Siri/main/siri3.list"
PARSER = "https://raw.githubusercontent.com/KOP-XIAO/QuantumultX/master/Scripts/resource-parser.js"
RULE_TYPES = {"host", "host-suffix", "host-keyword", "host-wildcard",
              "ip-cidr", "ip6-cidr", "ip-asn", "user-agent"}
SIRI_TYPES = {"domain": "host", "domain-suffix": "host-suffix",
              "domain-keyword": "host-keyword"}
# Expected policy names, not claims about unlock or actual egress.
PROBES = {
    "guzzoni.apple.com": "AI", "seed.siri.apple.com": "AI",
    "apple-relay.cloudflare.com": "AI", "gateway.icloud.com": "AI",
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
}


def active_lines(content):
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", ";", "//")):
            yield line


def parse_rules(content, siri=False):
    rules = []
    for line in active_lines(content):
        parts = fields(line)
        kind = parts[0].lower()
        if siri:
            if len(parts) != 2 or kind not in SIRI_TYPES:
                raise ValueError(f"Unexpected Siri rule: {line}")
            parts = [SIRI_TYPES[kind], parts[1], "AI"]
        else:
            if len(parts) < 3 or kind not in RULE_TYPES:
                raise ValueError(f"Invalid native QX rule: {line}")
            parts[0] = kind
            if parts[3:] and any(p not in {"no-resolve"} for p in parts[3:]):
                raise ValueError(f"Unknown QX rule option: {line}")
        kind, value, policy = parts[:3]
        if not value or not policy:
            raise ValueError("Empty rule value or policy")
        if kind in {"ip-cidr", "ip6-cidr"}:
            ipaddress.ip_network(value, strict=False)
        elif kind == "ip-asn":
            if not value.isdecimal():
                raise ValueError("Invalid ASN")
        rules.append((kind, value, policy))
    if not rules:
        raise ValueError("Empty ruleset")
    return rules


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "QX-Public-Profile-Check/1"}), timeout=30) as response:
        content = response.read()
        if response.status != 200 or response.url != url:
            raise ValueError(f"Unexpected response/redirect for {url}")
        return content, {"url": url, "resolved_url": response.url,
                         "status": response.status, "bytes": len(content),
                         "sha256": hashlib.sha256(content).hexdigest()}


def domain_matches(kind, value, domain):
    value, domain = value.lower(), domain.lower()
    return ((kind == "host" and domain == value)
            or (kind == "host-suffix" and (domain == value or domain.endswith("." + value)))
            or (kind == "host-keyword" and value in domain)
            or (kind == "host-wildcard" and fnmatch.fnmatchcase(domain, value)))


def route(domain, rules, fallback):
    for kind, value, policy in rules:
        if domain_matches(kind, value, domain):
            return policy
    return fallback


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
    return {"siri_rules": len(actual), "fictional_ss_nodes": parsed["nodes"]}


def online_check():
    sections = read_sections()
    resources = []
    for line in sections["filter_remote"]:
        url, *parts = fields(line)
        if url.startswith("https://"):
            resources.append((url, options(parts)))
    urls = [PARSER] + [url for url, _ in resources]
    with ThreadPoolExecutor(max_workers=6) as pool:
        fetched = dict(zip(urls, pool.map(fetch, urls)))
    receipt = {"verified_at": datetime.now(timezone.utc).isoformat(),
               "scope": "Public files and domain routing model; no QX import, user subscription, node or unlock test.",
               "profile_sha256": hashlib.sha256(PROFILE.read_bytes()).hexdigest(),
               "sources": [], "domain_probes": []}
    local = []
    fallback = None
    for line in sections["filter_local"]:
        parts = fields(line)
        if parts[0] == "final":
            fallback = parts[1]
        else:
            local.append(tuple(parts[:3]))
    ordered = list(local)
    siri_rules = None
    receipt["sources"].append(fetched[PARSER][1])
    for url, opts in resources:
        content, source = fetched[url]
        rules = parse_rules(content.decode("utf-8-sig"), siri=url == SIRI)
        source.update(rule_count=len(rules), types=sorted({r[0] for r in rules}))
        if url == SIRI:
            siri_rules = rules
            snapshot = [", ".join(r) for r in rules]
            source["native_snapshot"] = snapshot
            if list(active_lines("\n".join(sections["filter_local"])))[:len(snapshot)] != snapshot:
                raise ValueError("Upstream Siri changed: review and sync the local snapshot before release")
        receipt["sources"].append(source)
        if opts.get("enabled") == "true":
            if opts.get("inserted-resource") != "false":
                raise ValueError("Domain model requires local-first ordering")
            ordered.extend((kind, value, opts["force-policy"]) for kind, value, _ in rules)
    for domain, expected in PROBES.items():
        actual = route(domain, ordered, fallback)
        receipt["domain_probes"].append({"domain": domain, "expected": expected, "actual": actual})
        if actual != expected:
            raise ValueError(f"Routing regression for {domain}: expected {expected}, got {actual}")
    receipt["parser_check"] = check_parser(fetched[PARSER][0].decode(), fetched[SIRI][0].decode(), siri_rules)
    endpoint = "https://cp.cloudflare.com/generate_204"
    with urlopen(Request(endpoint, method="HEAD"), timeout=30) as response:
        if response.status != 204 or response.url != endpoint:
            raise ValueError("Latency endpoint no longer returns 204 without redirect")
        receipt["benchmark"] = {"url": endpoint, "method": "HEAD", "status": response.status,
                                "scope": "Current host connection only; no user nodes tested"}
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="Fetch public upstreams and test domain routing")
    parser.add_argument("--report", type=Path, help="Write public validation evidence as JSON")
    args = parser.parse_args()
    subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(ROOT),
                    "-p", "test_profile.py", "-v"], check=True)
    if args.online:
        receipt = online_check()
        if args.report:
            args.report.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        print(f"PASS: {len(receipt['sources'])} public sources; {len(PROBES)} domain probes; KOP parser; HEAD 204")
    elif args.report:
        parser.error("--report requires --online")


if __name__ == "__main__":
    main()
