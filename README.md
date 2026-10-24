# clinic-plugin-pack

**Your Claude Code, clinic-ready** — the first medical plugin pack for
Anthropic's official Claude Code plugins directory
([anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official)),
compiled from [packc](https://github.com/habib-analyst/packc)'s clinic pack.

## Why

The official plugin directory opened days ago. As of 2026-10-24 it lists
315 catalog entries and vendors 14 external + 39 internal plugins —
**zero of them medical** (verified by full-catalog sweep; see
`KILLGATE.md`). Anthropic's own README warns that plugins are untrusted
and unverified, so a medical pack has to bring its own proof. This one
does: it is compiled from a typed source and ships its conformance
evidence with it.

## What

`plugin/` is a complete, directory-shaped Claude Code plugin:

```
plugin/
├── .claude-plugin/plugin.json   # name: clinic-plugin-pack (immutable slug)
├── .mcp.json                    # registers the bundled clinic MCP server
├── README.md                    # pack documentation
├── LICENSE                      # MIT
├── skills/
│   ├── find-doctor/SKILL.md
│   ├── book-appointment/SKILL.md
│   ├── reschedule-appointment/SKILL.md
│   └── cancel-appointment/SKILL.md
├── mcp/
│   ├── clinic_mcp_server.py          # packc-generated MCP server (stdio)
│   └── test_clinic_conformance.py    # packc-generated contract tests
└── src/
    ├── clinic.pack              # typed source of truth
    └── clinic.SKILL.md          # packc's pack-level SKILL.md emission
```

The source of truth is `clinic.pack` (10 typed schemas, 4 skills, the
`care` flow, and an escalation policy: booking/cancellation default to
*confirm*, emergencies escalate to *human_only*). Everything in the
plugin is generated from it by [packc](https://github.com/habib-analyst/packc)
plus a small plugin-layout adapter — no hand-written skill files.

## Validation (measured 2026-10-24, this machine)

| Check | Result |
|---|---|
| packc typecheck of `clinic.pack` | OK — 10 schemas, 4 skills, 1 flow, 2 escalation rules |
| packc-generated conformance tests (MCP server) | **17/17 passed** |
| Project test suite (incl. live MCP stdio session) | **10/10 passed** |
| Structural validation vs official directory format | **35/35 checks, 0 dangling references** |
| Skill-load audit on the packed skills (his skill-load-test harness) | correct skill **ranked #1 on 4/4 tasks at catalog sizes 4, 20, 100** (recall@1 = recall@3 = 1.000; 0 outranked, 0 buried) |
| Reference-audit anchor | harness re-run on the source pack reproduced its published reference report *exactly* (tau 0.2833) |

Full numbers, method, and honest limits (including the tau/load-rate
nuance and the contract-shell nature of the tool handlers):
`BUILD_NOTES.md` and `results.json`. Audit reports live in `validation/`.

## Rebuild / re-verify

```bash
python3 tools/build_plugin.py        # packc check + emit + assemble plugin/
python3 tools/validate_plugin.py     # structural validation + ref scan
python3 tools/run_packed_audit.py    # skill-load audit on packed skills/
python3 -m pytest tests/ plugin/mcp/test_clinic_conformance.py
```

Requires Python 3.12 and read access to the source projects on this
machine (paths at the top of each tool). $0, CPU only.

## Status / honest limits

- The MCP tool handlers are typed **contract shells** (validate +
  documented sample output); a real deployment adds a `handlers` module
  with roster/scheduling logic.
- Front-desk logistics only — no triage, diagnosis, or medical advice.
- **Not yet submitted** to the directory. Submission goes through
  Anthropic's form; whether it accepts community submissions is a
  separate, still-open check. `marketplace-entry.draft.json` is the
  catalog entry in the directory's exact shape, ready for that step.

## License

MIT. Author: Habib Ur Rehman.
