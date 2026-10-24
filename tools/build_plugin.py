#!/usr/bin/env python3
"""Compile Habib's clinic.pack into the official Claude Code plugin layout.

Pipeline (all artifacts generated, none hand-written):
  1. `packc check`            — parse + typecheck the typed source.
  2. `packc emit mcp`         — plugin/mcp/clinic_mcp_server.py (verbatim).
  3. `packc emit tests`       — plugin/mcp/test_clinic_conformance.py (verbatim;
                                packc bakes the sibling server path into it).
  4. `packc emit skillmd`     — plugin/src/clinic.SKILL.md (packc's own
                                pack-level SKILL.md, kept as provenance).
  5. Per-skill SKILL.md files — generated here from the packc AST into
                                plugin/skills/<skill>/SKILL.md, the layout
                                the official directory uses (one SKILL.md per
                                skill directory). Descriptions carry each
                                skill's own declared trigger phrases.
  6. plugin.json / .mcp.json / README.md / LICENSE / src/clinic.pack.

Run:  python3 tools/build_plugin.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GOAL = os.path.expanduser(
    "~/workspace/goals/github-portfolio-linkedin-presence-buildout")
PACKC_DIR = os.path.join(GOAL, "hidden_files", "packc")
CLINIC_PACK = os.path.join(PACKC_DIR, "examples", "clinic.pack")
PLUGIN = os.path.join(ROOT, "plugin")
PLUGIN_NAME = "clinic-plugin-pack"


def run_packc(*argv: str) -> str:
    env = dict(os.environ, PYTHONPATH=PACKC_DIR)
    r = subprocess.run([sys.executable, "-m", "packc", *argv],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit("packc %s failed" % " ".join(argv))
    return (r.stdout + r.stderr).strip()


def skill_description(skill) -> str:
    """Official-style description: the skill's own text + its trigger phrases."""
    desc = (skill.description or "").strip()
    triggers = skill.triggers or []
    if triggers:
        quoted = ", ".join('"%s"' % t for t in triggers)
        desc = "%s This skill should be used when the user asks to %s." % (
            desc, quoted)
    return desc


def render_skill_md(pf, skill, schemas, esc_text, flow_lines) -> str:
    sys.path.insert(0, PACKC_DIR)
    from packc.emit_skillmd import _schema_table

    p = pf.pack
    lines = ["---",
             "name: %s" % skill.name,
             "description: %s" % json.dumps(skill_description(skill)),
             "version: %s" % p.version,
             "---", "",
             "# %s" % skill.name, "",
             skill.description or "", "",
             "Part of the **%s** pack (v%s) by %s — a clinic front-desk "
             "skill pack compiled with [packc](https://github.com/habib-analyst/packc) "
             "from the typed source `src/clinic.pack` shipped in this plugin."
             % (p.name, p.version, p.author), ""]
    if skill.triggers:
        lines += ["## When this skill applies", ""]
        lines += ['- The user asks to "%s".' % t for t in skill.triggers]
        lines.append("")
    if skill.tool:
        lines += ["## Tool", "",
                  "Backed by the MCP tool `%s` in this plugin's bundled "
                  "server (`mcp/clinic_mcp_server.py`, registered in "
                  "`.mcp.json`). The server validates every call against "
                  "the typed input schema before dispatch." % skill.tool, ""]
    if skill.input and skill.input in schemas:
        lines += ["## Input — `%s`" % skill.input, "",
                  _schema_table(schemas[skill.input]), ""]
    if skill.output and skill.output in schemas:
        lines += ["## Output — `%s`" % skill.output, "",
                  _schema_table(schemas[skill.output]), ""]
    if skill.steps:
        lines += ["## Steps", ""]
        lines += ["%d. %s" % (i + 1, s) for i, s in enumerate(skill.steps)]
        lines.append("")
    mine = []
    for fl in pf.flows:
        edges = ["- on `%s` → `%s`" % (e.event, e.target) for e in fl.edges]
        if fl.start == skill.name or any(skill.name in e for e in edges):
            mine.append("In flow `%s` (starts at `%s`):"
                        % (fl.name, fl.start))
            mine += edges
    if mine:
        lines += ["## Flow", ""] + mine + [""]
    lines += ["## Safety and escalation", "", esc_text, ""]
    return "\n".join(lines)


def escalation_text(pf) -> str:
    esc = pf.escalate
    if esc is None:
        return "No escalation policy is declared in the pack source."
    out = ["The pack source declares this escalation policy"
           " (context schema `%s`):" % esc.context, ""]
    if esc.defaults:
        out.append("Default tiers by action:")
        out += ["- `%s` → **%s**" % (a, t) for a, t in esc.defaults]
        out.append("")
    for r in esc.rules:
        if r.condition is None:
            out.append("- Rule `%s` (fallback): everything else → "
                       "**%s**." % (r.name, r.tier))
        else:
            c = r.condition
            v = c.value
            v = ("true" if v else "false") if isinstance(v, bool) else repr(v)
            out.append("- Rule `%s`: when `%s %s %s` → tier **%s**."
                       % (r.name, c.field, c.op, v, r.tier))
    out += ["",
            "Mutating actions (booking, cancellation) require confirmation "
            "by default, and the emergency rule escalates to a human. "
            "This pack handles front-desk logistics only; it does not give "
            "medical advice."]
    return "\n".join(out)


def main() -> int:
    os.makedirs(os.path.join(PLUGIN, ".claude-plugin"), exist_ok=True)
    os.makedirs(os.path.join(PLUGIN, "skills"), exist_ok=True)
    os.makedirs(os.path.join(PLUGIN, "mcp"), exist_ok=True)
    os.makedirs(os.path.join(PLUGIN, "src"), exist_ok=True)

    print(run_packc("check", CLINIC_PACK))
    print(run_packc("emit", "mcp", CLINIC_PACK, "-o",
                    os.path.join(PLUGIN, "mcp")))
    print(run_packc("emit", "tests", CLINIC_PACK, "-o",
                    os.path.join(PLUGIN, "mcp",
                                 "test_clinic_conformance.py")))
    print(run_packc("emit", "skillmd", CLINIC_PACK, "-o",
                    os.path.join(PLUGIN, "src")))
    shutil.copyfile(CLINIC_PACK, os.path.join(PLUGIN, "src", "clinic.pack"))
    shutil.copyfile(os.path.join(PACKC_DIR, "LICENSE"),
                    os.path.join(PLUGIN, "LICENSE"))

    sys.path.insert(0, PACKC_DIR)
    from packc.parser import parse_file
    pf = parse_file(CLINIC_PACK)
    schemas = {s.name: s for s in pf.schemas}
    esc_text = escalation_text(pf)
    flow_lines = []
    for fl in pf.flows:
        flow_lines.append("In flow `%s` (starts at `%s`):"
                          % (fl.name, fl.start))
        flow_lines += ["- on `%s` → `%s`" % (e.event, e.target)
                       for e in fl.edges]

    for skill in pf.skills:
        d = os.path.join(PLUGIN, "skills", skill.name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write(render_skill_md(pf, skill, schemas, esc_text,
                                     flow_lines))

    manifest = {
        "name": PLUGIN_NAME,
        "description": (
            "Clinic front-desk skills for Claude Code: find a doctor, book, "
            "reschedule, and cancel appointments. Compiled with packc from a "
            "typed source pack (schemas, flows, escalation policy) and "
            "shipped with the generated MCP tool server, so every tool call "
            "is validated against the pack's typed contracts. Booking and "
            "cancellation require confirmation by default; emergencies "
            "escalate to a human. Front-desk logistics only — no medical "
            "advice."),
        "version": pf.pack.version,
        "author": {"name": pf.pack.author},
        "license": "MIT",
        "keywords": ["medical", "clinic", "healthcare", "appointments",
                     "front-desk", "mcp", "skills"],
    }
    with open(os.path.join(PLUGIN, ".claude-plugin", "plugin.json"),
              "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")

    mcp_cfg = {"mcpServers": {"clinic": {
        "command": "python3",
        "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/clinic_mcp_server.py"]}}}
    with open(os.path.join(PLUGIN, ".mcp.json"), "w", encoding="utf-8") as fh:
        json.dump(mcp_cfg, fh, indent=2)
        fh.write("\n")

    print("skills written:", ", ".join(s.name for s in pf.skills))
    print("plugin assembled at", PLUGIN)
    return 0


if __name__ == "__main__":
    sys.exit(main())
