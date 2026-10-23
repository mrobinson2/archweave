---
name: archweave
description: "Turn system intent into architecture. Produce architecture, sequence, workflow, dataflow and lifecycle diagrams as static SVG and PNG from a prompt, in your organization's house style and vocabulary. Use when asked to draw, diagram, sketch, visualize or illustrate a system, request flow, process, pipeline or state model for a reference architecture, reference implementation, design pattern, implementation guide or ADR. Output is one SVG rendered to PNG; no interactive viewer. Not for dashboards, charts or slides."
license: MIT
metadata:
  version: "0.3.0"
  homepage: https://github.com/mrobinson2/archweave
---

# ArchWeave

Turn a prompt into one checked, house-styled static diagram: an SVG you author directly, plus a PNG rendered locally by headless Edge, Chrome or rsvg. Nothing leaves the machine. No external render services.

## Workflow (always in this order)

1. **Classify.** Pick one type from the router below. If ambiguous, ask one question; otherwise choose and name the choice in the title.
2. **Plan.** Write `plan.json` matching `schemas/<type>.schema.json`: nodes, zones or lanes, edges, legend, metadata stamp. Keep it small; it exists so the checker can catch structural mistakes before you draw.
3. **Read conventions.** Read `references/authoring-rules.md` once per session, `references/vocabulary.md` whenever the diagram touches named platform components, and `references/svg-conventions.md` before the first SVG of the session.
4. **Draw.** Write `<slug>.svg` by hand following `svg-conventions.md`. Paste the defs block from `assets/icons.xml` at the top. Use the shared symbols with `<use href="#i-...">`. Every node, zone and edge in `plan.json` must appear; nothing in the SVG may be absent from the plan.
5. **Check.** Run from the skill folder (Python 3.9+, standard library only):
   ```bash
   python scripts/check-diagram.py <folder>/plan.json <folder>/<slug>.svg
   ```
   Zero exit is the only pass. Fix every reported item and rerun. Never claim done after a failing check. If `cairosvg` happens to be installed the checker also writes the PNG; otherwise it prints a hint and you render in the next step.
6. **Render.** Windows:
   ```powershell
   scripts/render-png.ps1 <folder>/<slug>.svg
   ```
   macOS or Linux:
   ```bash
   scripts/render-png.sh <folder>/<slug>.svg
   ```
   If `scripts/render-png.*` are not present (Microsoft 365 skill sandbox), skip this step. The checker already wrote the PNG if `cairosvg` was available; otherwise deliver the SVG text and tell the user to render locally with `render-png` from the repository.
7. **Look.** Open the PNG and inspect it yourself. Look for text overflowing boxes, lines crossing text, arrowheads hidden behind boxes, orphaned nodes, missing legend, missing metadata stamp. Fix in the SVG, rerun check and render. Three repair rounds maximum; after that, report what still fails.
8. **Deliver.** Reply with the SVG and PNG paths, the diagram type, and any assumptions you made about platform components not stated in the prompt. In Microsoft 365, return the SVG as a file if the host allows it, otherwise as a code block, and always include the checker output.

Output folder: `out/<type>-<slug>-<YYYYMMDD-HHMM>/` under the workspace unless the user names a location. Keep `plan.json`, `<slug>.svg`, `<slug>.png` together.

## Type router

| Type | Use for | Schema | Example |
|---|---|---|---|
| `architecture` | Components, zones, hub and spoke, private endpoints, regions, control plane. Reference architectures and reference implementations. | `schemas/architecture.schema.json` | `examples/architecture-internal-api/` |
| `sequence` | Request lifecycle across participants, auth hops, retries, async returns. | `schemas/sequence.schema.json` | `examples/sequence-api-request/` |
| `workflow` | Processes with gates and swimlanes: intake, approval, pipeline, Golden Path, Day-2 runbook. | `schemas/workflow.schema.json` | `examples/workflow-golden-path/` |
| `dataflow` | Pipelines, telemetry paths, log forwarding, lineage, ingestion. | `schemas/dataflow.schema.json` | (author from rules) |
| `lifecycle` | State transitions: pattern status, deployment release, incident, ticket. | `schemas/lifecycle.schema.json` | (author from rules) |

Deployment views by DR strategy (Active/Active, Warm standby, Pilot light, Backup and restore) are `architecture` with a `dr_strategy` stamp and a secondary-region zone.

Each example folder holds `plan.json` and the finished diagram. The diagram is `<slug>.svg` in the repository and `<slug>.xml` in the Microsoft 365 skill package (same content, renamed so the package upload accepts it). Read it as text for structure; copy its structure, not its facts.

## Non-negotiables

- **Organization content, not vendor content.** Name the component as your organization names it (shared APIM, hub VNet, egress NVA, DNS steering, SIEM path), its position (hub or spoke, inherited or built) and its owner lane. A box that says only "API Management" with no organization context is a defect. The vocabulary file is the single place these facts live; if it is still the sample, say so in the reply.
- **Metadata stamp on every diagram.** Pattern ID, version, diagram name, DR strategy (if any), date, classification. Bottom-left, see svg-conventions.
- **Legend on every architecture and dataflow.** Color and line meaning per `authoring-rules.md`.
- **No external references.** No `<image href="http...">`, no web fonts, no external CSS. The checker fails on any `http` or `https` string.
- **No invented facts.** If the prompt does not give an address, hostname, SKU or DR strategy, use the vocabulary defaults or label the item `TBD` and say so in the reply. Never fabricate IPs or hostnames.
- **Static only.** No `<script>`, no `<animate>`, no CSS transitions.

## Working with Mermaid or an existing diagram

If the user supplies Mermaid, a photo or a screenshot, read it for topology and meaning, then author a fresh plan and SVG. Do not transcribe the source's styling.

## Repair rules

Fix the smallest neighborhood that clears the failure. Preserve meaning and every node from the plan. Typical fixes: shorten a label, widen a box, move a node one row, reroute a line with a jump arc, move a label off a line. Record nothing about the repair in the SVG.
