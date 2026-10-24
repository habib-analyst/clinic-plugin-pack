#!/usr/bin/env python3
"""Validate plugin/ against the official Claude Code plugin format.

The requirements encoded here were documented from the live official
directory (anthropics/claude-plugins-official) in KILLGATE.md:
repo README "Plugin Structure" + plugin.json/.mcp.json/SKILL.md files read
from serena, context7, example-plugin, hookify, claude-security, plugin-dev.

Also performs the install-layout simulation: every path referenced from the
pack's own files (via ${CLAUDE_PLUGIN_ROOT} or plugin-relative paths) must
exist at its packed location. Dangling reference bar: 0.

Usage: python3 tools/validate_plugin.py [--out validation/validation.json]
Exit code 0 iff every check passes.
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLUGIN = os.path.join(ROOT, "plugin")

SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
ALLOWED_MANIFEST_KEYS = {"name", "description", "author", "version",
                         "license", "keywords", "homepage", "repository",
                         "displayName"}

checks = []


def check(cid, ok, detail):
    checks.append({"id": cid, "ok": bool(ok), "detail": detail})
    print("%s %-34s %s" % ("PASS" if ok else "FAIL", cid, detail))


def frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None
    import yaml
    return yaml.safe_load(m.group(1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "validation",
                                                  "validation.json"))
    args = ap.parse_args()

    # ---- manifest ------------------------------------------------------
    pj_path = os.path.join(PLUGIN, ".claude-plugin", "plugin.json")
    check("manifest.exists", os.path.isfile(pj_path), pj_path)
    manifest = {}
    if os.path.isfile(pj_path):
        try:
            manifest = json.load(open(pj_path, encoding="utf-8"))
            check("manifest.valid_json", True, "plugin.json parses")
        except Exception as e:  # noqa: BLE001
            check("manifest.valid_json", False, str(e))
    if manifest:
        check("manifest.name_slug",
              bool(SLUG.match(manifest.get("name", ""))),
              "name=%r" % manifest.get("name"))
        check("manifest.description",
              bool((manifest.get("description") or "").strip()),
              "%d chars" % len(manifest.get("description", "")))
        check("manifest.author_name",
              bool((manifest.get("author") or {}).get("name")),
              "author=%r" % (manifest.get("author") or {}).get("name"))
        v = manifest.get("version")
        check("manifest.version_semver", v is None or bool(SEMVER.match(v)),
              "version=%r" % v)
        extra = set(manifest) - ALLOWED_MANIFEST_KEYS
        check("manifest.no_unknown_keys", not extra,
              "unknown keys: %s" % sorted(extra) if extra else "all known")

    # ---- layout ---------------------------------------------------------
    check("layout.readme", os.path.isfile(os.path.join(PLUGIN, "README.md")),
          "plugin/README.md")
    check("layout.license", os.path.isfile(os.path.join(PLUGIN, "LICENSE")),
          "plugin/LICENSE")

    skills_dir = os.path.join(PLUGIN, "skills")
    skill_dirs = sorted(d for d in os.listdir(skills_dir)
                        if os.path.isdir(os.path.join(skills_dir, d))) \
        if os.path.isdir(skills_dir) else []
    check("layout.skills_present", len(skill_dirs) > 0,
          "%d skill dirs" % len(skill_dirs))

    # skills declared in the typed source must match packed skill dirs 1:1
    pack_src = open(os.path.join(PLUGIN, "src", "clinic.pack"),
                    encoding="utf-8").read()
    declared = re.findall(r"^skill\s+([A-Za-z0-9_\-]+)\s*\{", pack_src,
                          re.MULTILINE)
    check("layout.skills_match_source", declared == skill_dirs or
          sorted(declared) == skill_dirs,
          "source=%s packed=%s" % (sorted(declared), skill_dirs))

    for d in skill_dirs:
        p = os.path.join(skills_dir, d, "SKILL.md")
        check("skill.%s.file" % d, os.path.isfile(p), p)
        if not os.path.isfile(p):
            continue
        fm = frontmatter(open(p, encoding="utf-8").read())
        check("skill.%s.frontmatter" % d, fm is not None,
              "YAML frontmatter parses")
        if fm:
            check("skill.%s.name_matches_dir" % d, fm.get("name") == d,
                  "frontmatter name=%r" % fm.get("name"))
            check("skill.%s.description" % d,
                  bool((fm.get("description") or "").strip()),
                  "%d chars" % len(fm.get("description") or ""))

    # ---- MCP ------------------------------------------------------------
    mcp_path = os.path.join(PLUGIN, ".mcp.json")
    check("mcp.exists", os.path.isfile(mcp_path), mcp_path)
    servers = {}
    if os.path.isfile(mcp_path):
        try:
            cfg = json.load(open(mcp_path, encoding="utf-8"))
            servers = cfg.get("mcpServers", cfg)
            check("mcp.valid_json", True, "servers: %s" % sorted(servers))
        except Exception as e:  # noqa: BLE001
            check("mcp.valid_json", False, str(e))
    server_files = []
    for name, srv in servers.items():
        has = ("command" in srv) or ("url" in srv)
        check("mcp.%s.entry_shape" % name, has,
              "command=%r url=%r" % (srv.get("command"), srv.get("url")))
        for a in srv.get("args", []):
            if isinstance(a, str) and "${CLAUDE_PLUGIN_ROOT}" in a:
                rel = a.replace("${CLAUDE_PLUGIN_ROOT}", "").lstrip("/")
                target = os.path.join(PLUGIN, rel)
                server_files.append(target)
                check("mcp.%s.server_file_exists" % name,
                      os.path.isfile(target), rel)
                if os.path.isfile(target):
                    try:
                        py_compile.compile(target, doraise=True)
                        check("mcp.%s.server_compiles" % name, True, rel)
                    except Exception as e:  # noqa: BLE001
                        check("mcp.%s.server_compiles" % name, False, str(e))

    # every tool the source declares must be served by the emitted server
    tools_declared = sorted(set(re.findall(r'tool:\s*"([^"]+)"', pack_src)))
    if server_files:
        src = open(server_files[0], encoding="utf-8").read()
        missing = [t for t in tools_declared
                   if ('"%s"' % t) not in src and ("'%s'" % t) not in src]
        check("mcp.all_pack_tools_served", not missing,
              "declared=%s missing=%s" % (tools_declared, missing))

    # ---- dangling references (install-layout simulation) ----------------
    ref_pat = re.compile(
        r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_.\-/]+)"
        r"|`((?:mcp|src|skills|\.claude-plugin)/[A-Za-z0-9_.\-/]+)`")
    refs = set()
    for base, _dirs, files in os.walk(PLUGIN):
        for fn in files:
            if not fn.endswith((".md", ".json")):
                continue
            text = open(os.path.join(base, fn), encoding="utf-8").read()
            for m in ref_pat.finditer(text):
                refs.add(m.group(1) or m.group(2))
    refs = {r for r in refs if "<" not in r and ">" not in r}
    dangling = [r for r in sorted(refs)
                if not os.path.exists(os.path.join(PLUGIN, r))]
    check("refs.none_dangling", not dangling,
          "%d references checked, %d dangling%s"
          % (len(refs), len(dangling),
             (": " + ", ".join(dangling)) if dangling else ""))

    # ---- marketplace draft coherence ------------------------------------
    draft = os.path.join(ROOT, "marketplace-entry.draft.json")
    if os.path.isfile(draft):
        entry = json.load(open(draft, encoding="utf-8"))
        check("marketplace.name_matches_manifest",
              entry.get("name") == manifest.get("name"),
              "entry name=%r" % entry.get("name"))

    passed = sum(1 for c in checks if c["ok"])
    report = {"checks_total": len(checks), "checks_passed": passed,
              "checks": checks,
              "references_checked": len(refs), "dangling": dangling}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("\n%d/%d checks passed; %d references checked, %d dangling"
          % (passed, len(checks), len(refs), len(dangling)))
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
