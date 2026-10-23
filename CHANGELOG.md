# Changelog

## 0.2.0 (2026-10-22)

- Checker ported from Node (`check-diagram.mjs`) to Python (`check-diagram.py`, 3.9+, standard library only). Same CLI, same checks, same messages, same exit codes; verified side by side on all examples and on broken variants before the Node file was removed.
- After a passing check the Python checker renders the PNG itself when `cairosvg` is importable; otherwise it prints a hint to run `render-png` locally.
- `m365/finish.ps1` calls `python`, falling back to `py -3`, instead of `node`.
- Docs and SKILL.md updated; SKILL.md commands are now relative to the skill folder.
- `dist/archweave-skill.zip` build: SKILL.md at the zip root with scripts, references, schemas, assets and examples beside it.

## 0.1.0 (2026-10-20)

First public release.

- Agent skill for architecture, sequence, workflow, dataflow and lifecycle diagrams as static SVG and PNG.
- Plan schemas, authoring rules, SVG conventions, vocabulary template with a fictional enterprise.
- Zero-dependency checker (plan rules, plan-to-SVG coverage, forbidden content, text overflow, metadata stamp).
- Local renderers: headless Edge or Chrome on Windows, rsvg or headless Chrome on macOS and Linux.
- 40-symbol icon library.
- Three worked examples: internal API architecture by DR strategy, API request sequence, Golden Path workflow.
- Hosts: VS Code GitHub Copilot agent mode, Claude Code, Microsoft 365 Copilot declarative agents (with a local finisher script).
