# clinic-plugin-pack — kill-gate record

Date: 2026-10-24 (Sat, PKT). Builder rule: kill-gate first, measured only, $0.

## Kill-Gate A — is the medical shelf in the official directory still empty?

Source: GitHub API (connector reads) on `anthropics/claude-plugins-official`,
HEAD `58267944f92187b7d6a1c822165c96c81c864806`, checked 2026-10-24.

Three layers checked:

1. **Vendored external plugins** (`external_plugins/`, 14 dirs):
   asana, context7, discord, fakechat, firebase, github, gitlab, imessage,
   laravel-boost, linear, playwright, serena, telegram, terraform.
   **None medical or clinical.**
2. **Vendored internal plugins** (`plugins/`, 39 dirs): language servers,
   code review/security, math, output styles, plugin-dev tooling.
   **None medical or clinical.**
3. **Full marketplace catalog** (`.claude-plugin/marketplace.json`, 315 entries,
   most of them remote-sourced): regex sweep for
   `medic|clinic|health|patient|diagnos|ehr|fhir|hl7|pharma|doctor|hospital|nurs|dental|radiolog|oncolog|surgery|therapy|wellness|hipaa`
   returned 5 hits, all false positives:
   - `azure` — "diagnos" = Azure diagnostics/deployment tooling.
   - `blackrock-advisor-center-plugin`, `intuit-quickbooks`, `monday-crm`,
     `pendo-analytics` — "health" = portfolio/business health.
   **No medical, clinical, healthcare, or patient-facing plugin exists in the
   catalog.** The catalog also has no medical category (categories present:
   automation, database, deployment, design, development, learning, location,
   math, migration, monitoring, productivity, security, testing).

**VERDICT A: PASS — the medical shelf is empty as of 2026-10-24.**

## Kill-Gate B — official format (from real plugins) + his assets exist

### Official plugin format, documented from the live repo

Repo README ("Plugin Structure") + files read from real plugins:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json      # Plugin metadata (REQUIRED)
├── .mcp.json            # MCP server configuration (optional)
├── commands/            # Slash commands (optional, legacy)
├── agents/              # Agent definitions (optional)
├── skills/              # Skill definitions (optional)
└── README.md            # Documentation
```

- **`.claude-plugin/plugin.json`** — required fields observed in every plugin:
  `name` (immutable slug), `description`, `author: {name, email?}`.
  Optional observed: `version`, `license`, `keywords`
  (e.g. `plugins/claude-security/.claude-plugin/plugin.json`).
  References read verbatim: `external_plugins/serena` (name/description/author),
  `external_plugins/context7`, `plugins/example-plugin`, `plugins/plugin-dev`.
- **`.mcp.json`** at plugin root — two shapes in the wild:
  wrapped `{"mcpServers": {name: server}}` (context7) and bare
  `{name: server}` (serena, example-plugin). Server entries are either
  `{"type": "http", "url": ...}` (hosted) or
  `{"command": ..., "args": [...]}` (local stdio, serena via `uvx`).
  This pack uses the wrapped shape with a local stdio server.
- **`skills/<skill-name>/SKILL.md`** — one directory per skill, `SKILL.md`
  required inside it; YAML frontmatter with `name` and `description`
  (official example phrases descriptions as triggers: *"This skill should be
  used when the user asks to ..."*) and optional `version`. Supporting files
  (`references/`, etc.) allowed beside `SKILL.md`.
  Reference: `plugins/example-plugin/skills/example-skill/SKILL.md`,
  `plugins/hookify/skills/writing-rules/`.
- **`commands/<name>.md`** is the legacy layout; the official example states
  new plugins should prefer the `skills/` directory format. This pack uses
  `skills/` only.
- **Marketplace entry** (`.claude-plugin/marketplace.json` in the directory
  repo): `{name, description, author?, category, source, homepage?, tags?}`.
  Vendored externals use `source: "./external_plugins/<name>"` and
  `tags: ["community-managed"]`; remote ones use
  `source: {source: "url"|"git-subdir", url, sha, path?, ref?}`.
  Plugin `name` is an **immutable slug** once published (repo README).
- **Install**: `/plugin install {name}@claude-plugins-official`.
- **Submission**: via the plugin directory submission form
  (https://clau.de/plugin-directory-submission); external plugins "must meet
  quality and security standards for approval" (repo README). Whether the form
  is open to community submitters is a separate check — **not** part of this
  build; submission remains an open step (see BUILD_NOTES.md).

### His source assets on this machine (inventoried, all real)

| Asset | Path | What it is |
|---|---|---|
| packc compiler | `~/workspace/goals/github-portfolio-linkedin-presence-buildout/hidden_files/packc/` | Typed skill-pack language + compiler: parser, typechecker, emitters for SKILL.md, MCP server, conformance tests. Published as github.com/habib-analyst/packc. |
| **Clinic pack source** | `.../hidden_files/packc/examples/clinic.pack` | `pack clinic v0.1.0`, author "Habib Ur Rehman": 4 skills (find-doctor, book-appointment, reschedule-appointment, cancel-appointment), 10 typed schemas, `care` flow, escalation policy (emergency → human_only; booking/cancel default to confirm). **This is the pack being compiled.** |
| skill-load-test harness | `~/workspace/goals/github-portfolio-linkedin-presence-buildout/build/skill-load-test/` | His skill-load conformance/audit harness (tfidf/bm25 routers, catalog loaders incl. SKILL.md-dir loader, failure taxonomy). Reference audit for clinic: `examples/reference_reports/clinic.json` (recall@1 = 1.0 at catalog sizes 4/20/100, 4 tasks, seed 7). Tasks: `examples/clinic_tasks.jsonl`. |
| agent-native-clinic | `~/workspace/goals/github-portfolio-linkedin-presence-buildout/build/agent-native-clinic/` | His clinic front-desk app (triage, appointments actions in TypeScript). Its `.mcp.json` only wires a dev tool (shadcn) — not a clinic MCP server, so the pack's MCP entry uses packc's emitted clinic server instead (see BUILD_NOTES). |

**VERDICT B: PASS — format documented from real directory plugins; the clinic
skill assets exist (clinic.pack + packc + skill-load-test). Nothing had to be
invented: the clinical content is his own clinic front-desk pack.**

## Build decision

Compile `clinic.pack` with packc into the official layout:

- `plugin/.claude-plugin/plugin.json` — name `clinic-plugin-pack` (the slug
  that claims the medical shelf), version from the pack (0.1.0), author
  Habib Ur Rehman.
- `plugin/skills/<skill>/SKILL.md` × 4 — one per clinic.pack skill, generated
  from the packc AST (descriptions carry the skills' own declared trigger
  phrases, per the official example's phrasing).
- `plugin/.mcp.json` — wraps packc's emitted MCP server
  (`plugin/mcp/clinic_mcp_server.py`, verbatim packc output; real MCP JSON-RPC
  over stdio: initialize / tools/list / tools/call, typed input validation).
- `plugin/src/clinic.pack` — the typed source of truth, for provenance and
  recompilation.
- Conformance: packc's own generated contract tests for the emitted server +
  his skill-load-test audit run against the **packed** `skills/` directory.
