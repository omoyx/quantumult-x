"""Check the public QX profile without opening subscriptions or running QX."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unittest
from urllib.parse import urlsplit


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
UNKNOWN_NAMES = ("c123s4", "JMS-01", "奶昔节点02", "BUS-01", "project-jpg", "未来机场 印度01", "Brasil 02")
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
            self.assertIn(opts["force-policy"], known)

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

    def test_siri_native_snapshot_is_complete_and_first(self):
        source = next(source for source in self.receipt["sources"] if source["url"].endswith("/siri3.list"))
        snapshot = source["native_snapshot"]
        self.assertEqual(len(snapshot), 32)
        self.assertEqual(self.sections["filter_local"][:len(snapshot)], snapshot)
        self.assertEqual(self.remote["Siri-AI"][1]["force-policy"], "AI")
        self.assertEqual(self.remote["Siri-AI"][1]["opt-parser"], "true")
        def local_domain_action(domain):
            for line in self.sections["filter_local"]:
                parts = fields(line)
                if len(parts) != 3:
                    continue
                kind, value, policy = parts
                if ((kind == "host" and domain == value)
                    or (kind == "host-suffix" and (domain == value or domain.endswith("." + value)))
                    or (kind == "host-keyword" and value in domain)):
                    return policy
            return None
        for rule in snapshot:
            kind, value, _ = fields(rule)
            domain = value if kind != "host-keyword" else value + ".example.com"
            self.assertEqual(local_domain_action(domain), "AI", domain)
        self.assertIsNone(local_domain_action("www.apple.com"))
        self.assertEqual(local_domain_action("api.perplexity.ai"), "AI服务")

    def test_specific_services_precede_general_rules_and_cn_fallback(self):
        order = list(self.remote)
        self.assertEqual(order[0], "Siri-AI")
        for specific, general in (("Siri-AI", "Apple"), ("Gemini", "Google"),
                                  ("YouTube", "Google"), ("Copilot", "Microsoft"),
                                  ("Netflix", "国际流媒体"), ("YouTube", "国际流媒体"),
                                  ("国际流媒体", "Apple")):
            self.assertLess(order.index(specific), order.index(general))
        for tag, (_, opts) in self.remote.items():
            self.assertEqual(opts["inserted-resource"], "false", tag)
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
