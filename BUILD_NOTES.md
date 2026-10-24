# clinic-plugin-pack — build notes (2026-10-24)

All numbers below were measured in this build on this machine. Nothing is
quoted from READMEs of the source projects without being re-run here.

## What was built

The first medical plugin pack for Anthropic's official Claude Code plugins
directory, compiled from Habib Ur Rehman's own clinic skill pack:

- Source of truth: `packc/examples/clinic.pack` — `pack clinic v0.1.0`,
  10 typed schemas, 4 skills (find-doctor, book-appointment,
  reschedule-appointment, cancel-appointment), the `care` flow, and an
  escalation policy (defaults: `message.send` auto, `appointment.book`
  confirm, `appointment.cancel` confirm; rule `emergency`:
  `is_emergency == true` → human_only; fallback → confirm).
- Compiler: his **packc** 0.1.0 (`check`, `emit mcp`, `emit tests`,
  `emit skillmd`) plus a plugin-layout adapter (`tools/build_plugin.py`)
  that renders one official-format `skills/<skill>/SKILL.md` per declared
  skill from the packc AST (frontmatter description = the skill's own
  description + its declared trigger phrases, in the official example's
  "should be used when the user asks to ..." phrasing).
- MCP server: packc's emitted `clinic_mcp_server.py`, verbatim. It is a
  real MCP server (JSON-RPC 2.0 over stdio: `initialize`, `tools/list`,
  `tools/call`), zero-dependency, and validates every call against the
  pack's typed input schemas. Registered in `plugin/.mcp.json` as server
  `clinic` via `${CLAUDE_PLUGIN_ROOT}/mcp/clinic_mcp_server.py`.

Decisions worth noting:

- **Name**: plugin slug `clinic-plugin-pack`. Directory plugin names are
  immutable once published (official repo README), so the slug itself is
  the shelf claim. The pack's internal name stays `clinic` (its packc
  identity; the MCP server reports pack `clinic` v0.1.0).
- **MCP source**: `agent-native-clinic`'s `.mcp.json` only wires the
  shadcn dev tool, so it had no clinic MCP server to wrap. packc's emitted
  server *is* his clinic MCP work (generated from clinic.pack), so the
  pack ships that.
- **`.mcp.json` shape**: the wrapped `{"mcpServers": {...}}` form (as in
  the directory's context7 plugin) rather than the bare-map form
  (serena/example-plugin). Both exist in the directory.
- **Marketplace entry**: `marketplace-entry.draft.json` mirrors the
  catalog entry shape. The catalog has **no medical category**; the draft
  uses `productivity` (closest existing) and says so in its `_comment`.

## Measured results

### Compile

```
packc check: OK — pack 'clinic' v0.1.0: 10 schemas, 4 skills, 1 flows, 2 escalation rules
```

### Conformance — packc-generated contract tests

The test file packc generates for the emitted server
(`plugin/mcp/test_clinic_conformance.py`, verbatim compiler output):
**17/17 passed** (`pytest`, 0.04 s).

### Conformance — project test suite

`tests/test_plugin_pack.py`: **10/10 passed** — manifest shape, validator
integration, per-skill fidelity to the source (descriptions lead with the
source text; every declared trigger present; tool + escalation policy
present in every SKILL.md), and a live MCP stdio session.

### Structural validation vs the official format

`tools/validate_plugin.py` encodes the requirements documented in
KILLGATE.md from the live directory: **35/35 checks passed**.
Install-layout simulation: **3 unique plugin-internal path references**
found across the pack's `.md`/`.json` files
(`${CLAUDE_PLUGIN_ROOT}/mcp/clinic_mcp_server.py`, `src/clinic.pack`,
`src/clinic.SKILL.md`), **0 dangling**. One validator bug was found and
fixed during the build (it searched the server source for double-quoted
tool names; the server registers tools single-quoted — the tools were all
present).

### Skill-load audit (his skill-load-test harness)

Config identical to the harness's published clinic reference: tfidf
router, catalog sizes 4/20/100, shortlist 3, max_loads 3, tau quantile
0.25, franchise distractors, seed 7, distractor pool = hostel-ops (14) +
restaurant (4) = 18 skills, tasks = `clinic_tasks.jsonl` (4 tasks).

**Anchor check** — re-running the harness CLI on the source `clinic.pack`
reproduced the published reference report *exactly* (tau 0.2833; every
scale metric identical). The harness measures what it claims.

**Packed audit** — golden catalog = the plugin's packed `skills/`
directory, loaded through the harness's SKILL.md-directory loader (only
frontmatter name + description visible, as a real loader sees them):

| Catalog size | recall@1 | recall@3 | loaded_rate | ok / skipped / outranked / buried |
|---|---|---|---|---|
| 4 | 1.000 | 1.000 | 0.750 | 3 / 1 / 0 / 0 |
| 20 | 1.000 | 1.000 | 0.500 | 2 / 2 / 0 / 0 |
| 100 | 1.000 | 1.000 | 0.750 | 3 / 1 / 0 / 0 |

Every one of the 12 task×scale rows ranked the correct skill **#1**
(12/12 rank-1, hit@1 true everywhere; 0 outranked, 0 buried at any size).

Honest nuance: the packed descriptions are longer than the source
one-liners (they carry the trigger phrases), so the harness calibrated a
higher tau (0.5803 vs 0.2833) and its load gate more often said "skip"
despite the rank-1 match — `loaded_rate` at size 20 is 0.500 vs the
reference's 1.000. Routing is perfect; the tau-gated *load decision* is
more conservative with official-style descriptions. Both numbers are
reported, not smoothed over.

### MCP stdio smoke (live session against the packed server)

- `initialize` → pack `clinic`, version `0.1.0`, 4 tools.
- `tools/list` → `doctors_search`, `appointment_book`,
  `appointment_reschedule`, `appointment_cancel`, each with a JSON
  `inputSchema`.
- `tools/call doctors_search {specialty: "cardiology", day: "monday"}`
  → OK; arguments validated and echoed; contract-shell output returned.
- `tools/call` with `specialty: 42` → JSON-RPC error **-32602**
  (argument validation failed). Missing required fields → -32602.
  Unknown tool → -32602.

## Honest limits

- The MCP server's tool handlers are packc **typed contract shells**:
  they validate arguments and return documented sample-shaped output.
  Real roster/scheduling business logic is author-supplied (the server
  supports a sibling `handlers` module). The pack README says this.
- The pack covers front-desk logistics (search/book/reschedule/cancel).
  It is not a triage, diagnostic, or medical-advice tool; the clinic
  app's `triage-assess` action was deliberately **not** turned into a
  plugin skill — it is not part of clinic.pack, and adding clinical
  content beyond his typed source was out of scope for this build.
- The generated conformance test bakes an absolute path to the server
  (packc's emit design); re-run `tools/build_plugin.py` after moving the
  project to regenerate it for the new location.
- **Directory submission was not done.** Submission is via Anthropic's
  form (https://clau.de/plugin-directory-submission); whether it is open
  to community submitters is unverified — that check is a separate step.
  No repo was created and nothing was pushed or posted by this build.
