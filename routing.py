"""Model QX sequential domain rules, including inserted remote resources.

This checks configuration intent, not DNS behavior, live QX or service access.
"""
import fnmatch
import ipaddress
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CUSTOM_URL = "https://raw.githubusercontent.com/omoyx/quantumult-x/main/rules/Custom.list"
CUSTOM_RESOURCE = (CUSTOM_URL + ", tag=自定义分流, update-interval=86400, "
                   "opt-parser=false, inserted-resource=true, enabled=true")
RULE_TYPES = {"host", "host-suffix", "host-keyword", "host-wildcard",
              "ip-cidr", "ip6-cidr", "ip-asn", "user-agent"}
SIRI_TYPES = {"domain": "host", "domain-suffix": "host-suffix",
              "domain-keyword": "host-keyword"}


def active_lines(content):
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", ";", "//")):
            yield line


def parse_rules(content, siri=False):
    rules = []
    for line in active_lines(content):
        parts = [part.strip() for part in line.split(",")]
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
        elif kind == "ip-asn" and not value.isdecimal():
            raise ValueError("Invalid ASN")
        rules.append((kind, value, policy))
    if not rules:
        raise ValueError("Empty ruleset")
    return rules


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


def ordered_rules(sections, remote_rules):
    """Inserted resources in list order, then local, then ordinary resources."""
    before, local, after = [], [], []
    fallback = None
    for line in sections["filter_local"]:
        parts = [part.strip() for part in line.split(",")]
        if parts[0].lower() == "final":
            fallback = parts[1]
        else:
            local.append(tuple(parts[:3]))
    for line in sections["filter_remote"]:
        url, *parts = [part.strip() for part in line.split(",")]
        opts = dict(part.split("=", 1) for part in parts if "=" in part)
        if opts.get("enabled", "true") == "false" or not url.startswith("https://"):
            continue
        rules = remote_rules[url]
        force = opts.get("force-policy")
        target = before if opts.get("inserted-resource") == "true" else after
        target.extend((kind, value, force or policy) for kind, value, policy in rules)
    return before + local + after, fallback
