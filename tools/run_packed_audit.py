#!/usr/bin/env python3
"""Skill-load conformance audit on the PACKED plugin skills.

Runs Habib's skill-load-test harness (build/skill-load-test) with the
plugin's own `skills/` directory as the golden catalog — loaded through the
harness's SKILL.md-directory loader, i.e. the packed artifact is audited
exactly as a loader sees it (frontmatter name + description only).

Configuration is identical to the harness's published clinic reference
audit (examples/reference_reports/clinic.json): tfidf router, catalog
sizes 4/20/100, shortlist 3, max_loads 3, tau quantile 0.25, franchise
distractor strategy, seed 7, distractor pool = hostel-ops.pack +
restaurant.pack, tasks = the harness's clinic_tasks.jsonl.

Usage: python3 tools/run_packed_audit.py
Writes validation/audit_packed.json and validation/audit_packed.md.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GOAL = os.path.expanduser(
    "~/workspace/goals/github-portfolio-linkedin-presence-buildout")
SLT_SRC = os.path.join(GOAL, "build", "skill-load-test", "src")
SLT_EXAMPLES = os.path.join(GOAL, "build", "skill-load-test", "examples")
PACKC_EXAMPLES = os.path.join(GOAL, "hidden_files", "packc", "examples")

sys.path.insert(0, SLT_SRC)

from skill_load_test.audit import AuditConfig, load_tasks, run_audit  # noqa: E402
from skill_load_test.catalog import load_any, load_skillmd_dir  # noqa: E402
from skill_load_test.report import render_json, render_markdown  # noqa: E402
from skill_load_test.routers import get_router  # noqa: E402


def main() -> int:
    golden = load_skillmd_dir(os.path.join(ROOT, "plugin", "skills"))
    for s in golden:
        s.golden = True
    pool = []
    for dp in ["hostel-ops.pack", "restaurant.pack"]:
        pool.extend(load_any(os.path.join(PACKC_EXAMPLES, dp)))
    pool = [s for s in pool if s.name not in {g.name for g in golden}]

    tasks = load_tasks(os.path.join(SLT_EXAMPLES, "clinic_tasks.jsonl"))
    config = AuditConfig(sizes=[4, 20, 100], router="tfidf",
                         topk_shortlist=3, max_loads=3, tau_quantile=0.25,
                         distractor_strategy="franchise", seed=7)
    result = run_audit(golden, pool, tasks, config, get_router("tfidf"))

    out_dir = os.path.join(ROOT, "validation")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "audit_packed.json"), "w",
              encoding="utf-8") as fh:
        fh.write(render_json(result))
    with open(os.path.join(out_dir, "audit_packed.md"), "w",
              encoding="utf-8") as fh:
        fh.write(render_markdown(result, "clinic-plugin-pack (packed)"))

    for size in sorted(result["scales"], key=int):
        sc = result["scales"][size]
        print("catalog %s: recall@1=%.3f recall@3=%.3f loaded_rate=%.3f "
              "taxonomy=%s" % (size, sc["recall@1"], sc["recall@3"],
                               sc["loaded_rate"], sc["taxonomy_counts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
