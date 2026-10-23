# SVG conventions

How to write the SVG so the checker passes, the PNG renders identically in Edge, Chrome and rsvg, and the result looks like a Lucidchart export.

## Skeleton

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="2000" height="1380" viewBox="0 0 2000 1380"
     font-family="Segoe UI, Helvetica, Arial, sans-serif" data-plan="plan.json">
  <title>rag-chatbot v1.0 RAG chatbot reference architecture</title>
  <defs> ... paste from assets/icons.svg ... </defs>
  <rect width="100%" height="100%" fill="#FFFFFF"/>
  <rect width="100%" height="100%" fill="url(#grid)" opacity="0.6"/>
  <!-- 1 title block -->
  <!-- 2 zones (back to front) -->
  <!-- 3 edges (so nodes draw over their ends) -->
  <!-- 4 nodes -->
  <!-- 5 badges and edge labels -->
  <!-- 6 legend, notes, metadata stamp -->
</svg>
```

Draw order matters: zones, then edges, then nodes, then labels. Edges under nodes hide arrowhead stubs. Labels last so nothing covers text.

## Node

```xml
<g id="n-apim-int" data-node="apim-int" transform="translate(880,200)">
  <rect width="160" height="110" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5" filter="url(#sh)"/>
  <use href="#i-apim" x="58" y="10" width="44" height="44"/>
  <text x="80" y="76" text-anchor="middle" font-size="15" font-weight="600" fill="#1F2937">Internal APIM</text>
  <text x="80" y="94" text-anchor="middle" font-size="12" fill="#6B7280">shared · hub · Premium</text>
</g>
```

Rules:
- `id="n-<planId>"` and `data-node="<planId>"` on the group. The checker matches these to `plan.json`.
- Width 140 to 200, height 100 to 120. Sublabel text width budget: `0.52 × 12 × chars ≤ width − 16`. Label: `0.52 × 15 × chars ≤ width − 16`.
- Shared or inherited components: fill `#F3F4F6`, stroke `#9CA3AF`. Edge or third party: stroke `#D97706`. AI: stroke `#6D44C9`.
- Private endpoint rows inside a PE subnet: 410 wide, 60 high, icon left, label and sublabel left-aligned at x=56.

## Zone

```xml
<g id="z-spoke" data-zone="spoke">
  <rect x="620" y="380" width="900" height="670" rx="6" fill="#F7F9FC" stroke="#0F6CBD" stroke-width="1.5"/>
  <text x="636" y="404" font-size="18" font-weight="600" fill="#0F6CBD">Spoke VNet · 10.230.4.0/22 · workload owned</text>
</g>
```

Secondary region: `stroke-dasharray="8 6"`. Nested zones allowed two deep (hub inside Azure, subnet inside spoke).

## Edge

```xml
<path id="e-user-edge" data-edge="user-edge" d="M165 442 H575 V152 H1000 V193"
      fill="none" stroke="#0F4C81" stroke-width="2.5" marker-end="url(#ab)"/>
```

- Orthogonal only (`H` and `V` segments). No diagonals, no curves except jump arcs.
- Jump arc where a later line crosses an earlier one: `H622 A8 8 0 0 1 638 1038 H...` (16 px wide arc, sweep 1 when traveling right, 0 when traveling left).
- End the path 2 px short of the target box edge; the marker's `refX` handles the overlap.
- Dashed telemetry: `stroke="#6B7280" stroke-width="2" stroke-dasharray="6 5" marker-end="url(#ag)"`.
- Edge label: `<text>` with white halo so it stays readable over lines:
  ```xml
  <text x="700" y="147" font-size="12" fill="#374151" paint-order="stroke" stroke="#FFFFFF" stroke-width="4">HTTPS 443 · Entra token</text>
  ```

## Badge

```xml
<g transform="translate(780,152)"><circle r="12" fill="#0F4C81"/><text y="4" text-anchor="middle" font-size="12" font-weight="700" fill="#FFF">4</text></g>
```
Blue for request steps, orange (`#D97706`) for ingestion letters, teal (`#1E8A7E`) for `T`.

## Legend

Bottom band, left of the stamp. One row per color meaning and one per line style, 12 px text. Then one line per numbered step: `1 User signs in with Entra · 2 Cloudflare origin allow-list · 3 ...`.

## Metadata stamp

```xml
<g id="meta" data-meta="true">
  <text x="40" y="1350" font-size="11" fill="#6B7280">rag-chatbot v1.0 · Diagram 1 of 6 · Reference architecture · Warm standby · 2026-10-20 · Internal · Draft</text>
</g>
```

## Forbidden

`<script>`, `<animate*>`, `<foreignObject>`, `<image>` with http(s), `@import`, `@font-face` with url, external `href`. The checker fails on any of them.

## PNG rendering notes

Edge headless rasterizes at `--window-size`; set it to the SVG width and height. Use `--force-device-scale-factor=1.3` for a 2600 px wide deck image. rsvg on macOS: `-w 2600`. Fonts: Segoe UI exists on Windows; the fallback chain keeps macOS renders close.
