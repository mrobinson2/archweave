# ArchWeave for Microsoft 365 Copilot

Two routes, not to be combined on one agent (Microsoft's preview does not allow skills and embedded files together):

- **Route A, skill package.** Agent Builder with custom skills (Frontier preview). Upload `dist/archweave-skill-agent-builder.zip`, paste `agent-instructions-skill.md`, add no other files. The checker runs in Copilot's sandbox. See "Skill package route" below.
- **Route B, knowledge files.** Any tenant. The agent reads the vocabulary and conventions as SharePoint knowledge and writes the SVG in chat; `finish.ps1` on the laptop checks it, renders the PNG with headless Edge, and opens it. You look, tell the agent what is wrong, it resends the SVG.

## What is shared with the VS Code version

Everything under `.github/skills/archweave/` is the single source: vocabulary, rules, SVG conventions, icons, schemas, examples, checker, renderer. This folder only adds an instruction file, an agent manifest template, and the local finisher.

| Step | VS Code Copilot or Claude Code | M365 Copilot declarative agent |
|---|---|---|
| Classify, plan, draw | agent, from SKILL.md | agent, from agent-instructions.md plus knowledge files |
| Check (`check-diagram.py`) | agent runs it | `finish.ps1` runs it if `plan.json` sits beside the SVG |
| Render PNG | agent runs `render-png.ps1` | `finish.ps1` runs `render-png.ps1` |
| Look and repair | agent views the PNG itself | you view the PNG, paste the checker output or describe the defect, agent resends SVG |
| Model | whatever the host offers | whatever the tenant exposes to declarative agents |

## Files

- `agent-instructions-skill.md`: Route A instructions, under 1,000 characters. Names the skill and nothing else.
- `agent-instructions.md`: Route B instructions, paste into Agent Builder or Copilot Studio. Under 8,000 characters.
- `declarativeAgent.json`: manifest template (schema v1.4) for a packaged agent via the Agents Toolkit. Replace the SharePoint URL placeholder.
- `finish.ps1`: clipboard or file SVG in, checked and rendered PNG out.

## Set up (Route B)

1. Upload to a SharePoint folder the agent can read: `references/vocabulary.md`, `references/authoring-rules.md`, `references/svg-conventions.md`, `assets/icons.xml`, and the three example SVGs from `examples/`.
2. Paste `agent-instructions.md` into the agent's instructions. Point knowledge at the folder.
3. Copy the whole repository to the laptop. Confirm Python 3.9 or later (`python` or `py -3`) and Edge. Run once:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\m365\finish.ps1 .\.github\skills\archweave\examples\architecture-internal-api\internal-api.svg
   ```
   A PNG should open. If Edge headless is blocked by policy, set `ARCHWEAVE_BROWSER` to Chrome, or open the SVG in PowerPoint and export.

## Use (Route B)

1. Ask: "Draw the Warm standby deployment view for internal-api."
2. The agent replies with the plan JSON and the SVG code block. Copy the SVG block.
3. Run `.\m365\finish.ps1` with nothing else; it reads the clipboard, saves to `out\`, checks, renders, opens.
4. For the full check, save the plan JSON as `plan.json` next to the SVG and rerun with the SVG path.
5. Paste checker failures or describe what looks wrong. The agent resends the whole SVG. Three rounds, then it reports what remains.

## Skill package route (Route A)

What Microsoft's docs state for the preview (checked 2026-10-22): zip up to 50 MB, 25 MB per file, 350 files, directory depth 3, SKILL.md under 20,000 characters with name and description in the front matter, supported resource types include `.md`, `.json`, `.xml`, `.png` and scripts `.py` and `.sh`; `.svg` and `.ps1` are not listed. Scripts run with no network and no package installs; only preinstalled packages are usable. Python version, file locations and whether script output comes back as a download are not documented.

Build and upload:
```bash
python .github/skills/archweave/scripts/build-zip.py --target agent-builder
# -> dist/archweave-skill-agent-builder.zip (examples as .xml, no render scripts, no example PNGs)
```
Agent Builder, Configure tab, Skills, Add, upload the zip. Paste `agent-instructions-skill.md` into Instructions. Add nothing else.

### Preview test plan

Run these on the Try it tab, in order. Stop at the first failure and report it.

1. Runtime probe. "Use the archweave skill. Run a Python script that prints sys.version, sys.executable, os.getcwd(), the files under the current directory two levels deep, and whether `import cairosvg` succeeds. Paste the raw output." Pass: a version string, a listing that includes SKILL.md and scripts/check-diagram.py, and true or false for cairosvg.
2. Package read. "Use the archweave skill. Quote the first heading of references/vocabulary.md and the id of the first symbol in assets/icons.xml." Pass: `# Vocabulary` and `i-user`.
3. Script on bundled data. "Use the archweave skill. Run scripts/check-diagram.py on examples/sequence-api-request/plan.json and examples/sequence-api-request/api-request.xml and paste the full output." Pass: `0 fail, 0 warn` then either the "PNG not rendered here" hint or a "rendered via cairosvg" line.
4. End to end. "Use the archweave skill to draw the Warm standby deployment view for internal-api. Write plan.json and the SVG, run the checker, and give me the checker output, the SVG as a file, and the PNG if one was made." Pass: 0 fail, the reply says "vocabulary is the sample", the stamp reads `internal-api v1.0 · ... · Warm standby`, and a file attachment appears or the SVG arrives in a code block.
5. Negative. "Change pattern_id in that plan.json to IMP.API.INTERNAL.1.0 and rerun the checker. Show the output and the exit code." Pass: `FAIL plan/meta: meta.pattern_id "IMP.API.INTERNAL.1.0" must be kebab-case` plus `stamp lacks pattern id`, exit code 1.

If the upload rejects the package, first remove the `license` and `metadata` keys from the SKILL.md front matter and retry; Microsoft's docs only require `name` and `description` and say nothing about other keys.

## Copilot Studio with code interpreter (optional)

Copilot Studio agents can run Python in a sandbox and return files, which could render the PNG without the laptop step. Diagram content then leaves the laptop into the tenant sandbox; internal hostnames and address ranges appear in these diagrams, so decide that with your security team. The laptop route keeps everything local.

## Limits of this route

- No automatic self-repair; you are the eyes. Expect two rounds per diagram.
- Declarative agents read knowledge files but may not read all of them every turn. If output drifts (vendor-generic labels, missing stamp), say "re-read vocabulary.md and svg-conventions.md" and ask again.
- Long SVGs can hit response length limits. Ask for a split into two diagrams.
- The plan schemas are advisory in chat; `finish.ps1` enforces them locally.
