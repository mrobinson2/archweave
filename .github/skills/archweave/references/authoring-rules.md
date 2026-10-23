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
