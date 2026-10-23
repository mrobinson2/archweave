# ArchWeave for Microsoft 365 Copilot

Same skill, different host. M365 Copilot cannot run scripts on your laptop, so the loop splits: the agent plans and writes the SVG in chat; `finish.ps1` on the laptop checks it, renders the PNG with headless Edge, and opens it. You look, tell the agent what is wrong, it resends the SVG.

## What is shared with the VS Code version

Everything under `.github/skills/archweave/` is the single source: vocabulary, rules, SVG conventions, icons, schemas, examples, checker, renderer. This folder only adds an instruction file, an agent manifest template, and the local finisher.

| Step | VS Code Copilot or Claude Code | M365 Copilot declarative agent |
|---|---|---|
| Classify, plan, draw | agent, from SKILL.md | agent, from agent-instructions.md plus knowledge files |
| Check (`check-diagram.mjs`) | agent runs it | `finish.ps1` runs it if `plan.json` sits beside the SVG |
| Render PNG | agent runs `render-png.ps1` | `finish.ps1` runs `render-png.ps1` |
| Look and repair | agent views the PNG itself | you view the PNG, paste the checker output or describe the defect, agent resends SVG |
| Model | whatever the host offers | whatever the tenant exposes to declarative agents |

## Files

- `agent-instructions.md`: paste into Agent Builder or Copilot Studio Instructions. Under 8,000 characters.
- `declarativeAgent.json`: manifest template (schema v1.4) for a packaged agent via the Agents Toolkit. Replace the SharePoint URL placeholder.
- `finish.ps1`: clipboard or file SVG in, checked and rendered PNG out.

## Set up

1. Upload to a SharePoint folder the agent can read: `references/vocabulary.md`, `references/authoring-rules.md`, `references/svg-conventions.md`, `assets/icons.svg`, and the three example SVGs from `examples/`.
2. Paste `agent-instructions.md` into the agent's instructions. Point knowledge at the folder.
3. Copy the whole repository to the laptop. Confirm Node 18 or later and Edge. Run once:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\m365\finish.ps1 .\.github\skills\archweave\examples\architecture-internal-api\internal-api.svg
   ```
   A PNG should open. If Edge headless is blocked by policy, set `ARCHWEAVE_BROWSER` to Chrome, or open the SVG in PowerPoint and export.

## Use

1. Ask: "Draw the Warm standby deployment view for internal-api."
2. The agent replies with the plan JSON and the SVG code block. Copy the SVG block.
3. Run `.\m365\finish.ps1` with nothing else; it reads the clipboard, saves to `out\`, checks, renders, opens.
4. For the full check, save the plan JSON as `plan.json` next to the SVG and rerun with the SVG path.
5. Paste checker failures or describe what looks wrong. The agent resends the whole SVG. Three rounds, then it reports what remains.

## Copilot Studio with code interpreter (optional)

Copilot Studio agents can run Python in a sandbox and return files, which could render the PNG without the laptop step. Diagram content then leaves the laptop into the tenant sandbox; internal hostnames and address ranges appear in these diagrams, so decide that with your security team. The laptop route keeps everything local.

## Limits of this route

- No automatic self-repair; you are the eyes. Expect two rounds per diagram.
- Declarative agents read knowledge files but may not read all of them every turn. If output drifts (vendor-generic labels, missing stamp), say "re-read vocabulary.md and svg-conventions.md" and ask again.
- Long SVGs can hit response length limits. Ask for a split into two diagrams.
- The plan schemas are advisory in chat; `finish.ps1` enforces them locally.
