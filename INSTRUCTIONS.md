# ArchWeave: install, configure, use

## 1. Prerequisites

| Need | Why | Check |
|---|---|---|
| Python 3.9 or later | runs the checker; standard library only, nothing to `pip install` | `python --version` (Windows: `py -3 --version`) |
| A browser or rsvg for PNG | Windows: Edge (ships with Windows) or Chrome. macOS/Linux: `rsvg-convert` (`brew install librsvg`) or Chrome/Chromium/Edge | `rsvg-convert --version` or the browser's path |
| An agent host | VS Code with GitHub Copilot agent mode, Claude Code, or Microsoft 365 Copilot | |

No npm, no pip packages, no network access at check or render time.

## 2. Install

### Option A: inside a repository (recommended for teams)

Put the skill at `.github/skills/archweave/` in the repository where diagrams will live. VS Code Copilot and Claude Code discover skills under `.github/skills/` (Claude Code also reads `.claude/skills/`). Commit it so everyone gets the same vocabulary.

From the release zip (SKILL.md is at the zip root):

```bash
curl -L -o archweave-skill.zip https://github.com/mrobinson2/archweave/releases/latest/download/archweave-skill.zip
curl -L -o archweave-skill.zip.sha256 https://github.com/mrobinson2/archweave/releases/latest/download/archweave-skill.zip.sha256
shasum -a 256 -c archweave-skill.zip.sha256     # Windows: certutil -hashfile archweave-skill.zip SHA256
mkdir -p your-repo/.github/skills/archweave && unzip -q archweave-skill.zip -d your-repo/.github/skills/archweave
```

Or from source (in this repository the skill lives at `skills/archweave/`, outside the dotfolder, so it is easy to browse):

```bash
git clone https://github.com/mrobinson2/archweave.git
cp -R archweave/skills/archweave  your-repo/.github/skills/archweave
```

### Option B: personal install

Unzip the release zip, or copy `archweave/` from a clone, into your user-level skills folder:

- Claude Code: `~/.claude/skills/archweave`
- GitHub Copilot: check the current VS Code docs for the user-level skills folder; recent builds also read `~/.claude/skills/`.

A specific version is at `https://github.com/mrobinson2/archweave/releases/download/v0.2.0/archweave-skill.zip`; `releases/latest/download/` always resolves to the newest release.

### Option C: Microsoft 365 Copilot

See section 6. Uses the same skill files as knowledge plus a short instruction block.

### Smoke test

```bash
cd archweave
python skills/archweave/scripts/check-diagram.py \
  skills/archweave/examples/architecture-internal-api/plan.json \
  skills/archweave/examples/architecture-internal-api/internal-api.svg
# expect: 0 fail, 0 warn, then a hint that the PNG is rendered locally (unless cairosvg is installed)
skills/archweave/scripts/render-png.sh skills/archweave/examples/architecture-internal-api/internal-api.svg
# Windows:
skills\archweave\scripts\render-png.ps1 skills\archweave\examples\architecture-internal-api\internal-api.svg
```

A PNG appears next to the SVG. If PowerShell blocks the script: `Set-ExecutionPolicy -Scope Process Bypass`.

## 3. Configure for your organization

Everything organization-specific lives in one file: `skills/archweave/references/vocabulary.md`. It ships with a fictional "Example Corporation" so the examples render. Replace it.

1. **Zones.** Keep the ids (`hub`, `spoke`, `edge`, `control`, `observability`, ...) and rewrite the labels and default content to match your landing zone.
2. **Components.** One row per platform component: the name your organization uses, icon id, color (ownership, not product), and the position-and-default sentence. That sentence is what the agent writes into sublabels and notes, so make it true: hub or spoke, inherited or built, who owns it, the SKU or address if it is fixed.
3. **Owner lanes.** List your real teams. Then update the `owner` enum in `schemas/common.schema.json` to the same list; the checker enforces it.
4. **DR strategies.** Rename to the names your resilience standard uses. Update the `dr_strategy` enum in `schemas/common.schema.json`.
5. **Pattern IDs.** Kebab-case slugs (`internal-api`, `rag-chatbot`) with an optional `version` for the footer. Adjust the `pattern_id` regex in `schemas/common.schema.json` if your catalog uses another form.
6. **Things never to draw.** Your non-negotiables. The agent treats this list as a hard rule.
7. **Classification.** The stamp text (`Internal`, `Confidential`, ...) is free text in the plan's `meta.classification`; the checker requires the same string to appear in the SVG stamp.

Optional:
- **Icons.** Add a `<symbol id="i-yourthing" viewBox="0 0 44 44">` to `assets/icons.xml`. Keep it free of `<image href="http...">`. Reference it from the vocabulary row. Official vendor sets and their terms are listed in section 8.
- **House style.** Palette, fonts and sizes are in `references/authoring-rules.md` and `references/svg-conventions.md`. Change the hex values in `assets/icons.xml` gradients and the rules together.
- **Renderer.** Set `ARCHWEAVE_BROWSER` to a browser executable if auto-detection misses it or policy blocks Edge headless. The skill itself makes no network calls, but a headless Edge or Chrome may contact its vendor on launch for updates or safe-browsing lists; point `ARCHWEAVE_BROWSER` at a locked-down Chromium, or use `rsvg-convert`, if that matters in your environment.

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
- "Same diagram in dark mode for the slide deck." (sets `meta.theme` to `dark`; palette in `references/authoring-rules.md`, section Theme).

Repairing by hand: edit the SVG, rerun the checker and the renderer. The agent will pick up your version on the next request if you point it at the folder.

## 5. The check-render loop by hand

```bash
python skills/archweave/scripts/check-diagram.py out/<folder>/plan.json out/<folder>/<slug>.svg
skills/archweave/scripts/render-png.sh out/<folder>/<slug>.svg 1.3      # second arg is scale
```

What the checker enforces: plan parses and matches the schema's intent (ids, references, label lengths, required legend); every plan node, zone and edge has a matching `data-node`, `data-zone`, `data-edge` in the SVG and nothing extra; nothing active or external (`<script>`, `<animate>`, `<set>`, `<foreignObject>`, DOCTYPE or entity declarations, `on*=` handlers, `javascript:`, `http(s)` and `file:` URLs, `@import`, `@font-face`, any `href` or `url()` that is not a local `#id` or `data:`); font floor 11 px; estimated text width inside node boxes; metadata stamp with pattern ID, date and classification. Exit code 0 is the only pass.

## 6. Use with Microsoft 365 Copilot

Two routes. Pick one per agent; do not combine them, since Microsoft's preview does not allow skills and embedded files on the same agent.

### Route A: skill package (Agent Builder, Frontier preview)

Requires a tenant enrolled in the Microsoft Frontier Program. The skill runs inside Copilot's script sandbox (no network, no package installs).

1. Build the package: `python skills/archweave/scripts/build-zip.py --target agent-builder` writes `dist/archweave-skill-agent-builder.zip`. It is the same skill with the example diagrams stored as `.xml`, and without the render scripts and example PNGs, because Microsoft's upload accepts only listed file types (`.svg` and `.ps1` are not on the list). The release page carries a prebuilt copy.
2. In Agent Builder, Configure tab, Skills, Add: upload the zip. Do not upload SKILL.md alone.
3. Paste `m365/agent-instructions-skill.md` into Instructions. Add no embedded files and no knowledge sources for the skill's own files; the package carries them.
4. On the Try it tab, run the prompts in `m365/README.md` under "Preview test plan". They confirm the sandbox runtime and whether files come back as downloads. If `cairosvg` is not preinstalled, the agent returns the SVG text and you render locally with `render-png` from this repository.

### Route B: knowledge files (any tenant)

M365 Copilot cannot run scripts on your laptop, so the loop splits: the agent writes the SVG in chat; `m365/finish.ps1` checks and renders it locally.

Set up once:
1. Upload to a SharePoint folder the agent can read: `references/vocabulary.md`, `references/authoring-rules.md`, `references/svg-conventions.md`, `assets/icons.xml`, and the three example SVGs.
2. Create an agent in Agent Builder (M365 Copilot) or Copilot Studio. Paste `m365/agent-instructions.md` into Instructions (under 8,000 characters). Point knowledge at the SharePoint folder. For a packaged agent, `m365/declarativeAgent.json` is a manifest template; replace the placeholder URL.
3. Copy this repository to the laptop. Run the smoke test from section 2 once.

Each diagram:
1. Ask the agent. It replies with the plan JSON and the SVG code block.
2. Copy the SVG block. Run `.\m365\finish.ps1` with no arguments; it reads the clipboard, saves under `out\`, checks what it can, renders, opens the PNG. Save the plan as `plan.json` beside the SVG and rerun with the SVG path for the full check.
3. Paste checker failures or describe what looks wrong. The agent resends the whole SVG. Expect two rounds instead of one, since you are the eyes.

Copilot Studio's code interpreter can render server-side, but diagram content then leaves the laptop. Decide that with your security team.

## 7. Writing a good prompt

Worked prompts for a dozen common diagrams, one per diagram type, are in `skills/archweave/references/prompt-cookbook.md`.

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

To add one: paste its paths into a new `<symbol>` in `assets/icons.xml`, keep the 44x44 viewBox convention, add a vocabulary row.

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

Issues and pull requests welcome. Keep the checker standard-library only (Python 3.9+), keep examples passing (`0 fail`), and keep organization-specific facts out of everything except `vocabulary.md` and the examples' fictional values.
