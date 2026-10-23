# ArchWeave: install, configure, use

## 1. Prerequisites

| Need | Why | Check |
|---|---|---|
| Node 18 or later | runs the checker; nothing to `npm install` | `node --version` |
| A browser or rsvg for PNG | Windows: Edge (ships with Windows) or Chrome. macOS/Linux: `rsvg-convert` (`brew install librsvg`) or Chrome/Chromium/Edge | `rsvg-convert --version` or the browser's path |
| An agent host | VS Code with GitHub Copilot agent mode, Claude Code, or Microsoft 365 Copilot | |

No Python, no npm packages, no network access at render time.

## 2. Install

### Option A: inside a repository (recommended for teams)

Copy `.github/skills/archweave/` into the repository where diagrams will live. VS Code Copilot and Claude Code discover skills under `.github/skills/` (Claude Code also reads `.claude/skills/`). Commit it so everyone gets the same vocabulary.

```bash
git clone https://github.com/mrobinson2/archweave.git
cp -R archweave/.github/skills/archweave  your-repo/.github/skills/archweave
```

### Option B: personal install

Copy `archweave/` to your user-level skills folder:

- Claude Code: `~/.claude/skills/archweave`
- GitHub Copilot: check the current VS Code docs for the user-level skills folder; recent builds also read `~/.claude/skills/`.

### Option C: Microsoft 365 Copilot

See section 6. Uses the same skill files as knowledge plus a short instruction block.

### Smoke test

```bash
cd archweave
node .github/skills/archweave/scripts/check-diagram.mjs \
  .github/skills/archweave/examples/architecture-internal-api/plan.json \
  .github/skills/archweave/examples/architecture-internal-api/internal-api.svg
# expect: 0 fail, 0 warn
.github/skills/archweave/scripts/render-png.sh .github/skills/archweave/examples/architecture-internal-api/internal-api.svg
# Windows:
.github\skills\archweave\scripts\render-png.ps1 .github\skills\archweave\examples\architecture-internal-api\internal-api.svg
```

A PNG appears next to the SVG. If PowerShell blocks the script: `Set-ExecutionPolicy -Scope Process Bypass`.

## 3. Configure for your organization

Everything organization-specific lives in one file: `.github/skills/archweave/references/vocabulary.md`. It ships with a fictional "Example Corporation" so the examples render. Replace it.

1. **Zones.** Keep the ids (`hub`, `spoke`, `edge`, `control`, `observability`, ...) and rewrite the labels and default content to match your landing zone.
2. **Components.** One row per platform component: the name your organization uses, icon id, color (ownership, not product), and the position-and-default sentence. That sentence is what the agent writes into sublabels and notes, so make it true: hub or spoke, inherited or built, who owns it, the SKU or address if it is fixed.
3. **Owner lanes.** List your real teams. Then update the `owner` enum in `schemas/common.schema.json` to the same list; the checker enforces it.
4. **DR strategies.** Rename to the names your resilience standard uses. Update the `dr_strategy` enum in `schemas/common.schema.json`.
5. **Pattern IDs.** Kebab-case slugs (`internal-api`, `rag-chatbot`) with an optional `version` for the footer. Adjust the `pattern_id` regex in `schemas/common.schema.json` if your catalog uses another form.
6. **Things never to draw.** Your non-negotiables. The agent treats this list as a hard rule.
7. **Classification.** The stamp text (`Internal`, `Confidential`, ...) is free text in the plan's `meta.classification`; the checker requires the same string to appear in the SVG stamp.

Optional:
- **Icons.** Add a `<symbol id="i-yourthing" viewBox="0 0 44 44">` to `assets/icons.svg`. Keep it free of `<image href="http...">`. Reference it from the vocabulary row. Official vendor sets and their terms are listed in section 8.
- **House style.** Palette, fonts and sizes are in `references/authoring-rules.md` and `references/svg-conventions.md`. Change the hex values in `assets/icons.svg` gradients and the rules together.
- **Renderer.** Set `ARCHWEAVE_BROWSER` to a browser executable if auto-detection misses it or policy blocks Edge headless.

## 4. Use in VS Code Copilot or Claude Code

1. Open the repository that contains the skill.
2. Pick a capable model in agent mode (Claude Opus 5.5 or equivalent).
3. Ask for a diagram. Name the pattern ID and DR strategy when you have them:

   > Use archweave to draw the Warm standby deployment view for payments-gateway: external partner API through the edge, shared external APIM, AKS in the spoke, Cosmos DB multi-region.

4. The agent classifies, writes `plan.json`, draws the SVG, runs the checker until it exits zero, renders, looks at the PNG, repairs up to three times, and replies with paths plus the assumptions it made.
5. Output lands in `out/<type>-<slug>-<timestamp>/` with `plan.json`, the SVG and the PNG. Drop the PNG into the deck, wiki or ADR. Keep the SVG for edits.

Prompts that work well:
- "Sequence diagram for the request path in that architecture, including the token validation hop."
- "Golden Path workflow for an internal API with the hand-offs the template removes struck through."
- "Dataflow from App Service diagnostics to the SIEM with the required log fields on the edges."
- "Lifecycle of a pattern from Draft to Deprecated with the gate owners."
- "Redraw this Mermaid in house style:" followed by the Mermaid block.

Repairing by hand: edit the SVG, rerun the checker and the renderer. The agent will pick up your version on the next request if you point it at the folder.

## 5. The check-render loop by hand

```bash
node .github/skills/archweave/scripts/check-diagram.mjs out/<folder>/plan.json out/<folder>/<slug>.svg
.github/skills/archweave/scripts/render-png.sh out/<folder>/<slug>.svg 1.3      # second arg is scale
```

What the checker enforces: plan parses and matches the schema's intent (ids, references, label lengths, required legend); every plan node, zone and edge has a matching `data-node`, `data-zone`, `data-edge` in the SVG and nothing extra; no `<script>`, `<animate>`, `<foreignObject>`, `http(s)` references, `@import` or `@font-face`; font floor 11 px; estimated text width inside node boxes; metadata stamp with pattern ID, date and classification. Exit code 0 is the only pass.

## 6. Use with Microsoft 365 Copilot

M365 Copilot cannot run scripts on your laptop, so the loop splits: the agent writes the SVG in chat; `m365/finish.ps1` checks and renders it locally.

Set up once:
1. Upload to a SharePoint folder the agent can read: `references/vocabulary.md`, `references/authoring-rules.md`, `references/svg-conventions.md`, `assets/icons.svg`, and the three example SVGs.
2. Create an agent in Agent Builder (M365 Copilot) or Copilot Studio. Paste `m365/agent-instructions.md` into Instructions (under 8,000 characters). Point knowledge at the SharePoint folder. For a packaged agent, `m365/declarativeAgent.json` is a manifest template; replace the placeholder URL.
3. Copy this repository to the laptop. Run the smoke test from section 2 once.

Each diagram:
1. Ask the agent. It replies with the plan JSON and the SVG code block.
2. Copy the SVG block. Run `.\m365\finish.ps1` with no arguments; it reads the clipboard, saves under `out\`, checks what it can, renders, opens the PNG. Save the plan as `plan.json` beside the SVG and rerun with the SVG path for the full check.
3. Paste checker failures or describe what looks wrong. The agent resends the whole SVG. Expect two rounds instead of one, since you are the eyes.

Copilot Studio's code interpreter can render server-side, but diagram content then leaves the laptop. Decide that with your security team.

## 7. Writing a good prompt

Give the agent what the vocabulary cannot know: the pattern ID, the DR strategy, which components are in scope, and anything that differs from the defaults ("this one uses AKS, not App Service", "partner-facing, so the external APIM"). Do not give it addresses or hostnames unless they are real; it will otherwise use the vocabulary defaults and say so.

Ask for one diagram per request. A reference implementation usually needs four to six: architecture, deployment by DR strategy, network topology, request sequence, dataflow, Day-2 workflow. Ask for them in that order; each later one can reference the earlier plan.

## 8. Official icon sets

The bundled glyphs are simplified originals so the skill works offline with no licensing questions. Swap in official marks where your audience expects them:

- Azure: https://learn.microsoft.com/azure/architecture/icons (SVG; use only in architecture diagrams and documentation; do not crop or alter).
- Cisco: https://www.cisco.com/c/en/us/about/brand-center/network-topology-icons.html (EPS, JPG, Visio, PowerPoint; free use, no alteration).
- F5: https://www.f5.com/resources/visio-stencils (hardware stencils).
- AWS: https://aws.amazon.com/architecture/icons/ (architecture icons, AWS terms).
- Google Cloud: https://cloud.google.com/icons (architecture icons, Google terms).
- Simple Icons: https://simpleicons.org (brand logos, CC0; check each brand's own guidelines).

To add one: paste its paths into a new `<symbol>` in `assets/icons.svg`, keep the 44x44 viewBox convention, add a vocabulary row.

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `svg/overflow` failures | label too long for the box | shorten the label or widen the box; the heuristic is 0.52 × font-size × characters |
| `svg/missing-node` | SVG group lacks `data-node="id"` matching the plan | add the attribute or remove the node from the plan |
| `svg/external` | an `http` string in the SVG | inline the asset or remove the link; only w3.org namespaces are allowed |
| PNG is blank or tiny | missing `width`/`height` on the `<svg>` root | add numeric width and height plus `viewBox` |
| `render-png.ps1` finds no browser | Edge not at the default path, or policy blocks headless | set `ARCHWEAVE_BROWSER`, or open the SVG in PowerPoint and export PNG |
| Agent produces vendor-generic boxes | vocabulary not read, or still the sample | ask it to re-read `vocabulary.md`; replace the sample values |
| Fonts differ between Windows and macOS renders | Segoe UI vs Helvetica fallback | expected; the fallback chain keeps widths close |

## 10. Contributing

Issues and pull requests welcome. Keep the checker dependency-free, keep examples passing (`0 fail`), and keep organization-specific facts out of everything except `vocabulary.md` and the examples' fictional values.
