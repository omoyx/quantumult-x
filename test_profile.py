"""Check the public QX profile without opening subscriptions or running QX."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
from urllib.parse import parse_qs, urlsplit

from routing import CUSTOM_RESOURCE, CUSTOM_URL, ordered_rules, parse_rules, route


ROOT = Path(__file__).resolve().parent
PROFILE = ROOT / "QuantumultX.conf"
RECEIPT = ROOT / "sources.json"

REGION_EXAMPLES = {
            "美国自动": ["JMS Los Angeles 01", "奶昔 美国-02", "🇺🇸 US 03", "未来机场 LAX01", "美國 04", "🇺🇸 洛杉矶①", "🇺🇸 洛杉矶②", "🇺🇸 洛杉矶③"],
            "日本自动": ["奶昔 东京01", "NewProvider JP-02", "🇯🇵 03", "JMS Osaka", "Japan NRT04", "🇯🇵 大阪"],
            "台湾自动": ["奶昔 台灣 01", "TW-02", "🇹🇼 03", "未来机场 Taipei", "臺北 04"],
            "香港自动": ["奶昔香港01", "NEW HK-02", "🇭🇰 03", "Hong Kong 04", "hkg05"],
            "新加坡自动": ["奶昔 狮城 01", "NEW SG-02", "🇸🇬 03", "Singapore04", "獅城 05"],
            "欧洲自动": ["JMS London", "DE-Frankfurt 02", "🇳🇱 03", "奶昔法兰克福04", "EU-05", "Paris 06", "英国07", "FI08", "🇨🇭 Zurich", "🇳🇱 荷兰"],
            "韩国自动": ["KR-01", "奶昔 首尔02", "🇰🇷 Seoul"],
            "加拿大自动": ["CA-01", "温哥华02", "🇨🇦 Toronto"],
            "澳大利亚自动": ["AU-01", "🇦🇺 Sydney", "奶昔 澳洲02"],
        }
UNKNOWN_NAMES = ("c123s4", "JMS-01", "奶昔节点02", "BUS-01", "project-jpg", "未来机场 印度01", "Brasil 02", "📥 下载")
METADATA_NAMES = ("剩余流量 50GB", "套餐到期 2027-01-01", "US 官网通知", "香港维护",
                  "Traffic: 100 GB", "Japan Expire: 2027", "Subscription update")


def read_sections():
    sections = {}
    for raw in PROFILE.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";", "//")):
            continue
        if line.startswith("["):
            name = line[1:-1]
            if name in sections:
                raise ValueError("duplicate section")
            sections[name] = []
        else:
            sections[name].append(line)
    return sections


def fields(line):
    return [part.strip() for part in line.split(",")]


def options(parts):
    return dict(part.split("=", 1) for part in parts if "=" in part)


def validate_probe_url(value):
    """Use plain HTTP for QX probe URL compatibility, independent of reachability."""
    parsed = urlsplit(value)
    if (parsed.scheme != "http" or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.fragment or any(char.isspace() for char in value)
            or (parsed.port is not None and not 1 <= parsed.port <= 65535)):
        raise ValueError("QX check URLs must be complete plain HTTP URLs without credentials or whitespace")
    return value


class QuantumultProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sections = read_sections()
        cls.policies = {}
        for line in cls.sections["policy"]:
            kind, _, body = line.partition("=")
            name, *parts = fields(body)
            if name in cls.policies:
                raise ValueError("duplicate policy")
            cls.policies[name] = (kind.strip(), parts)
        cls.regexes = {
            name: re.compile(options(parts)["server-tag-regex"])
            for name, (_, parts) in cls.policies.items()
            if "server-tag-regex" in options(parts)
        }
        cls.remote = {
            options(fields(line)[1:])["tag"]: (fields(line)[0], options(fields(line)[1:]))
            for line in cls.sections["filter_remote"]
        }
        cls.receipt = json.loads(RECEIPT.read_text())

    def test_probe_urls_use_qx_compatible_http(self):
        general = {key.strip(): value.strip() for key, value in options(self.sections["general"]).items()}
        for key in ("server_check_url", "network_check_url"):
            self.assertEqual(validate_probe_url(general[key]), general[key])
        for value in ("https://cp.cloudflare.com/generate_204", "http:///generate_204",
                      "http://cp.cloudflare.com/\ngenerate_204", "http://user:pass@example.com/check"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_probe_url(value)

    def test_profile_contains_no_subscriptions_nodes_or_interception(self):
        self.assertEqual(set(self.sections), {
            "general", "dns", "policy", "server_remote", "server_local",
            "filter_remote", "filter_local", "rewrite_remote", "rewrite_local",
            "task_local", "http_backend", "mitm",
        })
        for section in ("server_remote", "server_local", "rewrite_remote",
                        "rewrite_local", "task_local", "http_backend", "mitm"):
            self.assertEqual(self.sections[section], [], section)
        active = "\n".join(line for lines in self.sections.values() for line in lines)
        self.assertNotRegex(active, r"(?i)(password|passphrase|p12|token|uuid)\s*=")
        self.assertNotIn("__QX_PRIVATE_", active)
        for url in re.findall(r"https?://[^,\s]+", active):
            parsed = urlsplit(url)
            self.assertIsNone(parsed.username)
            self.assertIsNone(parsed.password)
            self.assertEqual(parsed.query, "")
            self.assertEqual(parsed.fragment, "")
            self.assertIn(parsed.hostname, {
                "raw.githubusercontent.com", "www.apple.com", "cp.cloudflare.com",
            })

    def test_policy_and_filter_references_exist_and_have_no_cycles(self):
        known = set(self.policies) | {"direct", "proxy", "reject"}
        graph = {}
        for name, (kind, parts) in self.policies.items():
            self.assertIn(kind, {"static", "url-latency-benchmark"})
            refs = [part for part in parts if "=" not in part]
            self.assertTrue(set(refs) <= known, (name, refs))
            graph[name] = [ref for ref in refs if ref in self.policies]
            self.assertNotIn("resource-tag-regex", options(parts), name)
        def visit(name, path):
            self.assertNotIn(name, path, (name, path))
            for ref in graph[name]:
                visit(ref, path + [name])
        for name in graph:
            visit(name, [])
        for line in self.sections["filter_local"]:
            self.assertIn(fields(line)[-1], known, line)
        for _, opts in self.remote.values():
            if "force-policy" in opts:
                self.assertIn(opts["force-policy"], known)
        for filename in ("Custom.list", "Custom-compat.list"):
            for _, _, policy in parse_rules((ROOT / "rules" / filename).read_text()):
                self.assertIn(policy, known)

    def test_region_examples_from_multiple_providers_and_naming_styles(self):
        examples = REGION_EXAMPLES
        for group, names in examples.items():
            for name in names:
                with self.subTest(group=group, name=name):
                    matched = {key for key, regex in self.regexes.items() if regex.search(name)}
                    self.assertEqual(matched, {group, "全球自动", "手动节点"})

    def test_unknown_regions_stay_visible_without_guessing(self):
        for name in UNKNOWN_NAMES:
            with self.subTest(name=name):
                matched = {key for key, regex in self.regexes.items() if regex.search(name)}
                self.assertEqual(matched, {"全球自动", "手动节点"})

    def test_metadata_is_excluded_from_all_groups(self):
        for name in METADATA_NAMES:
            self.assertFalse(any(regex.search(name) for regex in self.regexes.values()), name)

    @unittest.skipUnless(sys.platform == "darwin" and shutil.which("xcrun"), "Apple Foundation requires macOS")
    def test_region_patterns_in_native_apple_icu(self):
        cases = []
        for group, names in REGION_EXAMPLES.items():
            cases.extend({"name": name, "groups": [group, "全球自动", "手动节点"]} for name in names)
        cases.extend({"name": name, "groups": ["全球自动", "手动节点"]} for name in UNKNOWN_NAMES)
        cases.extend({"name": name, "groups": []} for name in METADATA_NAMES)
        subprocess.run(["xcrun", "swift", str(ROOT / "check_regex.swift"), str(PROFILE)],
                       input=json.dumps(cases, ensure_ascii=False), text=True, check=True)

    def test_latency_policy_uses_active_checks_and_switch_tolerance(self):
        groups = [name for name, (kind, _) in self.policies.items() if kind == "url-latency-benchmark"]
        self.assertEqual(len(groups), 10)
        for name in groups:
            opts = options(self.policies[name][1])
            self.assertEqual(opts["check-interval"], "600")
            self.assertEqual(opts["tolerance"], "50")
            self.assertEqual(opts["alive-checking"], "false")
        self.assertEqual(self.policies["AI"][1][0], "美国自动")
        self.assertTrue({"direct", "proxy", "reject"} <= set(self.policies["AI"][1]))

    def test_managed_siri_rules_preserve_compatibility_except_shared_gateway(self):
        source = next(source for source in self.receipt["sources"] if source["url"].endswith("/siri3.list"))
        snapshot = source["native_snapshot"]
        self.assertEqual(len(snapshot), 32)
        rules = parse_rules((ROOT / "rules/Custom.list").read_text())
        for rule in snapshot:
            kind, value, _ = fields(rule)
            expected = "direct" if value == "gateway.icloud.com" else "AI"
            self.assertIn((kind, value, expected), rules)
            domain = value if kind != "host-keyword" else value + ".example.com"
            self.assertEqual(route(domain, rules, None), expected, domain)
        self.assertIsNone(route("www.apple.com", rules, None))
        self.assertEqual(route("api.perplexity.ai", rules, None), "AI服务")
        self.assertFalse(any("AI" in line for line in self.sections["filter_local"]))

    def test_addition_overrides_existing_local_gateway_and_google_rules(self):
        snapshot = next(s["native_snapshot"] for s in self.receipt["sources"]
                        if s["url"].endswith("/siri3.list"))
        custom = parse_rules((ROOT / "rules/Custom.list").read_text())
        google_url = "https://example.invalid/Google.list"
        old = {"filter_local": snapshot + ["final, 兜底"], "filter_remote": [
            CUSTOM_RESOURCE, google_url + ", force-policy=Google, inserted-resource=false"]}
        supplied = {CUSTOM_URL: custom,
                    google_url: [("host-suffix", "googleapis.com", "proxy")]}
        rules, fallback = ordered_rules(old, supplied)
        for domain, expected in {
            "gateway.icloud.com": "direct", "seed.siri.apple.com": "AI",
            "apple-relay.cloudflare.com": "AI", "api.perplexity.ai": "AI服务",
            "gcs-us-00003.content-storage-upload.googleapis.com": "direct",
            "storage.googleapis.com": "Google"}.items():
            self.assertEqual(route(domain, rules, fallback), expected, domain)
        old["filter_remote"][0] = CUSTOM_RESOURCE.replace("inserted-resource=true", "inserted-resource=false")
        wrong_order, fallback = ordered_rules(old, supplied)
        self.assertEqual(route("gateway.icloud.com", wrong_order, fallback), "AI")

    def test_direct_exceptions_are_narrow_and_compat_only_changes_gateway(self):
        primary = parse_rules((ROOT / "rules/Custom.list").read_text())
        compat = parse_rules((ROOT / "rules/Custom-compat.list").read_text())
        self.assertEqual(len(primary), len(set(primary)))
        self.assertEqual(set(primary) - set(compat), {("host", "gateway.icloud.com", "direct")})
        self.assertEqual(set(compat) - set(primary), {("host", "gateway.icloud.com", "AI")})
        self.assertEqual(compat, [(kind, value, "AI" if value == "gateway.icloud.com" else policy)
                                  for kind, value, policy in primary])
        for domain in ("iosapps.itunes.apple.com", "ussea3.icloud-content.com",
                       "edge-297.hkhkg2.icloud-content.com", "example.icloud-content.com.cn",
                       "gcs-us-00003.content-storage-upload.googleapis.com"):
            self.assertEqual(route(domain, primary, None), "direct")
            self.assertEqual(route(domain, compat, None), "direct")
        for domain in ("googleapis.com", "storage.googleapis.com", "www.icloud.com",
                       "www.apple.com", "example.synology.me", "17.248.188.147",
                       "content-storage-upload.googleapis.com.example.org"):
            self.assertIsNone(route(domain, primary, None), domain)
        self.assertTrue(all(kind in {"host", "host-suffix", "host-keyword"}
                            for kind, _, _ in primary))

    def test_install_links_only_add_filter_resources_with_mixed_policies(self):
        readme = (ROOT / "README.md").read_text()
        links = re.findall(r"\]\((https://quantumult.app/x/open-app/add-resource\?remote-resource=[^)]+)\)", readme)
        self.assertEqual(len(links), 2)
        for link, filename in zip(links, ("Custom.list", "Custom-compat.list")):
            data = json.loads(parse_qs(urlsplit(link).query)["remote-resource"][0])
            self.assertEqual(set(data), {"filter_remote"})
            self.assertEqual(data["filter_remote"], [CUSTOM_RESOURCE.replace("Custom.list", filename)])

    def test_specific_services_precede_general_rules_and_cn_fallback(self):
        order = list(self.remote)
        self.assertEqual(order[0], "自定义分流")
        self.assertEqual(self.remote["自定义分流"][0], CUSTOM_URL)
        self.assertEqual(self.remote["自定义分流"][1]["opt-parser"], "false")
        self.assertNotIn("force-policy", self.remote["自定义分流"][1])
        for specific, general in (("自定义分流", "Apple"), ("Gemini", "Google"),
                                  ("YouTube", "Google"), ("Copilot", "Microsoft"),
                                  ("Netflix", "国际流媒体"), ("YouTube", "国际流媒体"),
                                  ("国际流媒体", "Apple")):
            self.assertLess(order.index(specific), order.index(general))
        for tag, (_, opts) in self.remote.items():
            self.assertEqual(opts["inserted-resource"], "true" if tag == "自定义分流" else "false", tag)
        self.assertEqual(self.remote["Apple"][1]["force-policy"], "Apple")
        self.assertEqual(self.policies["Apple"][1][0], "direct")
        self.assertEqual(order[-1], "CN")
        self.assertEqual(self.remote["CN"][0], "FILTER_REGION")
        self.assertFalse(any(line.lower().startswith("geoip,") for line in self.sections["filter_local"]))
        self.assertEqual(self.sections["filter_local"][-1], "final, 兜底")
        self.assertEqual(self.remote["广告拦截"][1]["enabled"], "false")

    def test_public_rule_urls_were_checked_and_native_rules_use_no_parser(self):
        checked = {source["url"]: source for source in self.receipt["sources"]}
        native_types = {"host", "host-suffix", "host-keyword", "host-wildcard",
                        "ip-cidr", "ip6-cidr", "ip-asn", "user-agent"}
        for tag, (url, opts) in self.remote.items():
            if not url.startswith("https://"):
                continue
            if url == CUSTOM_URL:
                self.assertEqual(opts["opt-parser"], "false")
                continue
            with self.subTest(tag=tag):
                source = checked[url]
                self.assertEqual(source["status"], 200)
                self.assertEqual(source["resolved_url"], url)
                self.assertRegex(source["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(source["rule_count"], 0)
                if tag != "Siri-AI":
                    self.assertEqual(opts["opt-parser"], "false")
                    self.assertTrue(set(source["types"]) <= native_types)


if __name__ == "__main__":
    unittest.main()
