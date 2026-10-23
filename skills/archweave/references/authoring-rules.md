# Authoring rules

Read once per session before the first plan. These are the rules the checker cannot measure but a reviewer will notice. Adapted from Archify's authoring defaults and trimmed for static output.

## Composition

- Lead with the main journey. For architecture, the reader's eye should follow the user request from the left edge (or top) through edge, hub, spoke, data. Secondary paths (ingestion, telemetry, control plane) run in their own corridor and are numbered or lettered separately.
- Group by real boundary, not by convenience. A zone means one of: network boundary (VNet, subnet), ownership boundary (hub team vs app team), region, trust boundary (internet vs corporate), persistence boundary. Name the kind in the plan.
- Separate roles when grouping would hide ownership, trust, lifecycle, or persistence.
- Nothing without a reason. Every node either sits on a path or explains a constraint. Delete decorative nodes.
- Cards and notes answer a reader question ("why is Key Vault access policy, not RBAC?"). They never replace topology.
- There is no node, edge or zone quota. Fit the question. Typical reference architecture: 12 to 30 nodes, 3 to 7 zones.

## Labels

- Node label: product or component name as your organization calls it. Sublabel: organization-specific configuration in one line (SKU, scope, position, address range, owner). Example: label `Internal APIM`, sublabel `shared, hub, Premium, 10.0.4.0/26`.
- Edge label: verb plus protocol or condition when it changes behavior: `HTTPS 443, mTLS`, `blob created event`, `PIM 4h session`. Omit the label only when both ends make it obvious.
- Short beats complete. Budget roughly 0.52 × font-size pixels per character. Two-line labels are fine; three are not.
- No vendor marketing words. No "secure", "scalable", "robust", "modern".

## Layout

- Place by connection first, then assign coordinates. Main path neighbors adjacent in reading order. Stores and branches directly above or below their owner, centered, one straight segment. Returns on the side with no branches.
- Fan-out: a side with k connectors needs at least 32 + 14 × (k − 1) px.
- Trace every non-main edge before writing coordinates: its straight or one-bend corridor must not pass another node or cross another edge. If it does, move the endpoint that is off the main path.
- Crossings that cannot be avoided get a jump arc (`A8 8 0 0 1`) on the line drawn later.
- Canvas: 1600 to 2000 wide for architecture, aspect roughly 3:2 or 16:10. Sequence and lifecycle may be taller than wide. Keep 40 px margin.
- Fonts: title 30, zone titles 18 to 20, node labels 15, sublabels 12, edge labels 12, notes 11. Nothing below 11.

## Color and line meaning (fixed, goes in legend)

| Meaning | Fill or stroke | Gradient id |
|---|---|---|
| Azure resource owned by the workload (spoke) | blue | `az` |
| Shared or inherited platform component (hub, Security, SRE) | grey | `gy` |
| Edge or third party (CDN, partner) | orange | `or` |
| AI or data service | purple | `pu` |
| Observability and telemetry | teal | `az2` |
| Request path | solid blue 2.5 px, marker `ab` | |
| Ingestion or batch | solid orange 2.5 px, marker `ao` | |
| Telemetry, control plane, inherited | dashed grey 2 px, marker `ag` | |
| Private endpoint | small pe icon on the subnet edge | |

Zones: fill `#F7F9FC` to `#EEF3F8`, stroke 1.5 px, 6 px radius, title top-left in zone color. Secondary region zone uses dashed stroke.

## Numbering

Request path steps get numbered badges 1..n in blue. Ingestion or batch gets letters A..n in orange. Telemetry gets a single `T` badge in teal. The legend lists what the numbers mean in one line each.

## Metadata stamp

Bottom-left block, 11 px grey: `rag-chatbot v1.0 · Diagram 1 of 6 · Reference architecture · Warm standby · 2026-10-20 · Internal · Draft`. The checker requires at least the pattern ID, the version when the plan sets one, the date and the classification.

## Sequence specifics

- 3 to 8 participants left to right in order of first use. Lifelines dashed grey.
- Message label above the arrow, left-aligned at source. Return messages dashed.
- Activation bars only where the participant does work. Notes to the right of the message, max two lines.
- Group boxes (alt, loop, retry) with a label tab top-left.

## Workflow specifics

- Swimlanes are owner lanes from `vocabulary.md`. One lane per owner that actually acts.
- Gates are diamonds with the gate owner in the sublabel and the evidence it needs on the exit edge.
- Hand-offs that the Golden Path removes are drawn once with a red strike and listed in a note; this is the point of the diagram.

## Dataflow specifics

- Stages left to right, 2 to 5. Sources at left, sinks at right. Every edge labeled with what moves (`common-schema JSON`, `blob`, `embedding vectors`).
- Classification of data marked on the edge where it changes (`PII`, `Confidential`).

## Lifecycle specifics

- Happy path left to right on one row. Failure and wait states below. Terminal states double-bordered.
- Every transition labeled with the trigger and the actor.

## Theme

Default is light. Use dark when the prompt says dark mode, dark theme, or the output goes on dark slides. Set `meta.theme` to `dark` in the plan; the checker then expects the dark canvas color and the word `Dark` in the stamp. Same layout, same icons, same line meanings; only the palette changes.

| Role | Light | Dark |
|---|---|---|
| Canvas rect | `#FFFFFF` | `#0F172A` |
| Grid pattern | `url(#grid)` | `url(#grid-d)` |
| Title text | `#111827` | `#F1F5F9` |
| Subtitle, stamp, sublabel, dashed telemetry and control lines | `#6B7280` / `#4B5563` | `#94A3B8` |
| Node label text | `#1F2937` | `#F1F5F9` |
| Edge label text | `#374151` | `#CBD5E1` |
| Edge label halo (`stroke` with `paint-order="stroke"`) | `#FFFFFF` | `#0F172A` |
| Workload node fill / stroke | `#FFFFFF` / `#CBD5E1` | `#1E293B` / `#475569` |
| Shared or inherited node fill / stroke | `#F3F4F6` / `#9CA3AF` | `#334155` / `#64748B` |
| Zone fill (workload) / stroke | `#F7F9FC` / `#0F6CBD` | `#1E293B` / `#60A5FA` |
| Zone fill (platform) / stroke | `#F3F4F6` / `#6B7280` | `#1F2937` / `#64748B` |
| Observability zone fill / stroke | `#F0FAF8` / `#1E8A7E` | `#0F2A28` / `#2DD4BF` |
| Request line and badge | `#0F4C81`, marker `ab` | `#60A5FA`, marker `ab-d` |
| Ingestion line and badge | `#D97706`, marker `ao` | `#F59E0B`, marker `ao-d` |
| Telemetry or control line | `#6B7280` or `#1E8A7E`, marker `ag` | `#94A3B8` or `#2DD4BF`, marker `ag-d` |
| Note fill / stroke / title text | `#FFFBEB` / `#F59E0B` / `#92400E` | `#3B2F0B` / `#F59E0B` / `#FCD34D` |
| Removed hand-off fill / stroke | `#FEF2F2` / `#B91C1C` | `#3F1D1D` / `#F87171` |
| Legend box fill / stroke | `#FFFFFF` / `#E5E7EB` | `#1E293B` / `#334155` |
| Sequence activation (hub / workload) | `#D1D5DB` / `#BFDBFE` | `#475569` / `#1E3A8A` |
| Badge text | `#FFF` | `#FFF` |

Icon gradients are unchanged; they read well on both canvases. The drop shadow filter is harmless on dark.
