#!/usr/bin/env python3
# ArchWeave diagram checker v0.2. Python 3.9+, standard library only.
# Usage: python check-diagram.py <plan.json> <diagram.svg>
# Exit 0 only when every check passes. Prints one line per finding.
#
# Checks:
#   plan: parses, schema_version/diagram_type, meta stamp fields, unique ids,
#         edge endpoints exist, zone parents exist, lane/stage/zone refs exist,
#         label length budgets, lifecycle main_path refers to states.
#   svg:  well-formed enough (balanced root), width/height/viewBox, <title>,
#         no script/animate/foreignObject/external href/http(s),
#         every plan node present as data-node, every zone as data-zone,
#         every edge as data-edge (architecture/dataflow/workflow/lifecycle),
#         every sequence participant as data-node, message as data-edge,
#         data-meta stamp containing pattern_id, date, meta.classification and v<version> when set,
#         text overflow heuristic for node labels/sublabels inside data-node groups,
#         fonts not smaller than 11px, SVG elements not in plan (data-node unknown).
#
# Optional render: after a passing check, if cairosvg imports, <slug>.png is written
# beside the SVG at 1.3x scale. Otherwise a one-line hint says to render locally.

import json
import math
import re
import sys
from pathlib import Path

argv = sys.argv[1:]
if len(argv) < 2 or not argv[0] or not argv[1]:
    print('usage: check-diagram.py <plan.json> <diagram.svg>', file=sys.stderr)
    sys.exit(2)
plan_path, svg_path = argv[0], argv[1]

findings = []


def fail(code, msg):
    findings.append(('FAIL', code, msg))


def warn(code, msg):
    findings.append(('WARN', code, msg))


def truthy(v):
    """JavaScript truthiness for JSON values: None, False, 0, '' are falsy; {} and [] are truthy."""
    if v is None or v is False or v == '':
        return False
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v == 0:
        return False
    return True


def js_str(v):
    """String(v) as JavaScript would print it inside a template literal."""
    if v is None:
        return 'undefined'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def js_round(x):
    return int(math.floor(x + 0.5))


def report():
    fails = [f for f in findings if f[0] == 'FAIL']
    warns = [f for f in findings if f[0] == 'WARN']
    for level, code, msg in findings:
        print(f'{level} {code}: {msg}')
    print(f'\n{len(fails)} fail, {len(warns)} warn  ({plan_path} / {svg_path})')
    sys.exit(1 if fails else 0)


# ---------- plan ----------
try:
    plan = json.loads(Path(plan_path).read_text(encoding='utf-8'))
except Exception as e:  # parse or read error
    fail('plan/parse', f'cannot parse {plan_path}: {e}')
    report()

if not isinstance(plan, dict):
    plan = {}

TYPES = ['architecture', 'sequence', 'workflow', 'dataflow', 'lifecycle']
sv = plan.get('schema_version')
if not (isinstance(sv, (int, float)) and not isinstance(sv, bool) and sv == 1):
    fail('plan/schema-version', 'schema_version must be 1')
if plan.get('diagram_type') not in TYPES:
    fail('plan/type', f"diagram_type must be one of {', '.join(TYPES)}")
dtype = plan.get('diagram_type')

meta = plan.get('meta') or {}
if not isinstance(meta, dict):
    meta = {}
for k in ['title', 'pattern_id', 'date', 'classification', 'output']:
    if not truthy(meta.get(k)):
        fail('plan/meta', f'meta.{k} missing')
if truthy(meta.get('pattern_id')) and not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', js_str(meta.get('pattern_id'))):
    fail('plan/meta', f'meta.pattern_id "{js_str(meta.get("pattern_id"))}" must be kebab-case (letters, digits, single hyphens)')
if 'version' in meta and not re.fullmatch(r'[0-9]+(\.[0-9]+){0,2}', js_str(meta.get('version'))):
    fail('plan/meta', f'meta.version "{js_str(meta.get("version"))}" must look like 1.0')
if truthy(meta.get('date')) and not re.fullmatch(r'20[0-9]{2}-[0-9]{2}-[0-9]{2}', js_str(meta.get('date'))):
    fail('plan/meta', 'meta.date must be YYYY-MM-DD')
if truthy(meta.get('classification')) and not js_str(meta.get('classification')).strip():
    fail('plan/meta', 'meta.classification must not be blank')

ID = re.compile(r'[a-z][a-z0-9-]*')
ids = {}


def collect(items, kind):
    for item in items or []:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str):
            fail(f'plan/{kind}', f'{kind} item without id')
            continue
        if not ID.fullmatch(item['id']):
            fail(f'plan/{kind}', f'{kind} id "{item["id"]}" must be lowercase kebab')
        if item['id'] in ids:
            fail('plan/id', f'duplicate id "{item["id"]}" ({ids[item["id"]]} and {kind})')
        ids[item['id']] = kind


node_kind = {'architecture': 'nodes', 'sequence': 'participants', 'workflow': 'nodes', 'dataflow': 'nodes', 'lifecycle': 'states'}.get(dtype)
edge_kind = {'architecture': 'edges', 'sequence': 'messages', 'workflow': 'edges', 'dataflow': 'flows', 'lifecycle': 'transitions'}.get(dtype)
container_kind = {'architecture': 'zones', 'sequence': None, 'workflow': 'lanes', 'dataflow': 'stages', 'lifecycle': None}.get(dtype)

collect(plan.get(container_kind) if container_kind else None, container_kind)
collect(plan.get(node_kind) if node_kind else None, node_kind)
collect(plan.get(edge_kind) if edge_kind else None, edge_kind)
collect(plan.get('notes'), 'notes')
collect(plan.get('groups'), 'groups')

nodes = [n for n in (plan.get(node_kind) or []) if isinstance(n, dict)] if node_kind else []
edges = [e for e in (plan.get(edge_kind) or []) if isinstance(e, dict)] if edge_kind else []
containers = [c for c in (plan.get(container_kind) or []) if isinstance(c, dict)] if container_kind else []
node_ids = {n.get('id') for n in nodes}
container_ids = {c.get('id') for c in containers}

if len(nodes) < 2:
    fail(f'plan/{js_str(node_kind)}', f'need at least 2 {js_str(node_kind)}')
if len(edges) < 1:
    fail(f'plan/{js_str(edge_kind)}', f'need at least 1 {js_str(edge_kind)}')

ref_key = {'architecture': 'zone', 'workflow': 'lane', 'dataflow': 'stage'}.get(dtype)
for n in nodes:
    nid = js_str(n.get('id'))
    if not truthy(n.get('label')):
        fail('plan/label', f'{nid} has no label')
    if truthy(n.get('label')) and len(js_str(n.get('label'))) > 60:
        fail('plan/label', f'{nid} label longer than 60 chars')
    if truthy(n.get('sublabel')) and len(js_str(n.get('sublabel'))) > 70:
        fail('plan/label', f'{nid} sublabel longer than 70 chars')
    if ref_key and n.get(ref_key) not in container_ids:
        fail('plan/ref', f'{nid}.{ref_key} "{js_str(n.get(ref_key))}" is not a {container_kind} id')
    if dtype == 'architecture':
        for k in ['color', 'icon', 'owner']:
            if not truthy(n.get(k)):
                fail('plan/node', f'{nid}.{k} missing')
        if truthy(n.get('icon')) and not re.fullmatch(r'i-[a-z0-9]+', js_str(n.get('icon'))):
            fail('plan/node', f'{nid}.icon "{js_str(n.get("icon"))}" must be i-<name>')
for c in containers:
    if truthy(c.get('parent')) and c.get('parent') not in container_ids:
        fail('plan/ref', f'{container_kind} {js_str(c.get("id"))}.parent "{js_str(c.get("parent"))}" unknown')
for e in edges:
    eid = js_str(e.get('id'))
    if e.get('from') not in node_ids:
        fail('plan/ref', f'{eid}.from "{js_str(e.get("from"))}" is not a {node_kind} id')
    if e.get('to') not in node_ids:
        fail('plan/ref', f'{eid}.to "{js_str(e.get("to"))}" is not a {node_kind} id')
    if e.get('from') == e.get('to') and dtype != 'lifecycle':
        fail('plan/edge', f'{eid} is a self-loop')
    if truthy(e.get('label')) and len(js_str(e.get('label'))) > 70:
        fail('plan/label', f'{eid} label longer than 70 chars')
    if dtype in ('dataflow', 'lifecycle') and not truthy(e.get('label')):
        fail('plan/label', f'{eid} needs a label in {dtype}')
if dtype == 'lifecycle':
    for s in plan.get('main_path') or []:
        if s not in node_ids:
            fail('plan/ref', f'main_path "{js_str(s)}" is not a state id')
if dtype == 'sequence':
    for g in plan.get('groups') or []:
        if not isinstance(g, dict):
            continue
        mids = {m.get('id') for m in edges}
        if g.get('from_message') not in mids:
            fail('plan/ref', f'group {js_str(g.get("id"))}.from_message unknown')
        if g.get('to_message') not in mids:
            fail('plan/ref', f'group {js_str(g.get("id"))}.to_message unknown')
if dtype in ('architecture', 'dataflow') and not truthy(plan.get('legend')):
    fail('plan/legend', f'{dtype} requires legend')

# orphan nodes
touched = set()
for e in edges:
    touched.add(e.get('from'))
    touched.add(e.get('to'))
for n in nodes:
    if n.get('id') not in touched:
        warn('plan/orphan', f'{js_str(n.get("id"))} has no {edge_kind}')

# ---------- svg ----------
try:
    svg = Path(svg_path).read_text(encoding='utf-8')
except Exception as e:
    fail('svg/read', f'cannot read {svg_path}: {e}')
    report()

if not re.match(r'\s*(<\?xml[^>]*\?>\s*)?(<!--[\s\S]*?-->\s*)*<svg[\s>]', svg):
    fail('svg/root', 'file must start with <svg')
if not re.search(r'</svg>\s*\Z', svg):
    fail('svg/root', 'file must end with </svg>')
m_root = re.search(r'<svg[^>]*>', svg)
root_tag = m_root.group(0) if m_root else ''
if not re.search(r'\bwidth="\d+(\.\d+)?"', root_tag) or not re.search(r'\bheight="\d+(\.\d+)?"', root_tag):
    fail('svg/size', '<svg> needs numeric width and height')
if not re.search(r'\bviewBox="', root_tag):
    fail('svg/size', '<svg> needs viewBox')
if not re.search(r'<title>[^<]+</title>', svg):
    fail('svg/title', 'missing <title>')

for pattern, code, msg in [
    (r'<script[\s>]', 'svg/forbidden', '<script> not allowed'),
    (r'<animate', 'svg/forbidden', '<animate*> not allowed'),
    (r'<foreignObject', 'svg/forbidden', '<foreignObject> not allowed'),
    (r'https?://(?!www\.w3\.org/)', 'svg/external', 'external http(s) reference found (only w3.org namespaces allowed)'),
    (r'@import|@font-face', 'svg/external', '@import or @font-face not allowed'),
    (r'<image[^>]*href="(?!data:)', 'svg/external', '<image> must be inline data: or absent'),
]:
    if re.search(pattern, svg, re.IGNORECASE):
        fail(code, msg)

# tag balance (rough)
opens = len(re.findall(r'<g[\s>]', svg))
closes = len(re.findall(r'</g>', svg))
if opens != closes:
    fail('svg/balance', f'<g> open/close mismatch {opens}/{closes}')


# plan <-> svg coverage
def attr_set(attr):
    return list(dict.fromkeys(re.findall(attr + r'="([^"]+)"', svg)))


svg_nodes = attr_set('data-node')
svg_edges = attr_set('data-edge')
svg_zones = attr_set('data-zone')
edge_ids = {e.get('id') for e in edges}

for n in nodes:
    if n.get('id') not in svg_nodes:
        fail('svg/missing-node', f'plan {node_kind} "{js_str(n.get("id"))}" has no data-node in SVG')
for e in edges:
    if e.get('id') not in svg_edges:
        fail('svg/missing-edge', f'plan {edge_kind} "{js_str(e.get("id"))}" has no data-edge in SVG')
if dtype == 'architecture':
    for z in containers:
        if z.get('id') not in svg_zones:
            fail('svg/missing-zone', f'plan zone "{js_str(z.get("id"))}" has no data-zone in SVG')
if dtype in ('workflow', 'dataflow'):
    for z in containers:
        if z.get('id') not in svg_zones:
            fail('svg/missing-zone', f'plan {container_kind} "{js_str(z.get("id"))}" has no data-zone in SVG')
for i in svg_nodes:
    if i not in node_ids:
        fail('svg/unknown-node', f'SVG data-node "{i}" not in plan')
for i in svg_edges:
    if i not in edge_ids:
        fail('svg/unknown-edge', f'SVG data-edge "{i}" not in plan')

# metadata stamp
m_meta = re.search(r'<g[^>]*data-meta="true"[^>]*>[\s\S]*?</g>', svg)
meta_block = m_meta.group(0) if m_meta else ''
if not meta_block:
    fail('svg/meta', 'missing <g data-meta="true"> stamp')
else:
    if js_str(meta.get('pattern_id')) not in meta_block:
        fail('svg/meta', f'stamp lacks pattern id {js_str(meta.get("pattern_id"))}')
    if js_str(meta.get('date')) not in meta_block:
        fail('svg/meta', f'stamp lacks date {js_str(meta.get("date"))}')
    if truthy(meta.get('version')) and f'v{js_str(meta.get("version"))}' not in meta_block:
        fail('svg/meta', f'stamp lacks version v{js_str(meta.get("version"))}')
    if truthy(meta.get('classification')) and js_str(meta.get('classification')) not in meta_block:
        fail('svg/meta', f'stamp lacks classification "{js_str(meta.get("classification"))}"')

# body without <defs> (symbols may carry their own font sizes and rects)
body = re.sub(r'<defs>[\s\S]*?</defs>', '', svg)

# font floor
for m in re.finditer(r'font-size="(\d+(?:\.\d+)?)"', body):
    if float(m.group(1)) < 11:
        fail('svg/font', f'font-size {m.group(1)} below 11px floor')
        break

# text overflow heuristic inside data-node groups:
# group's first <rect width=W>, each <text font-size=S text-anchor=middle>: 0.52*S*len must be <= W-12
for m in re.finditer(r'<g[^>]*data-node="([^"]+)"[^>]*>([\s\S]*?)</g>', body):
    gid, group = m.group(1), m.group(2)
    mw = re.search(r'<rect[^>]*?(?<![-\w])width="(\d+(?:\.\d+)?)"', group)
    w = float(mw.group(1)) if mw else 0.0
    if not w:
        continue
    for t in re.finditer(r'<text([^>]*)>([^<]*)</text>', group):
        attrs = t.group(1)
        txt = re.sub(r'&[a-z]+;', 'x', t.group(2).replace('&amp;', '&'))
        ms = re.search(r'font-size="(\d+(?:\.\d+)?)"', attrs)
        size = float(ms.group(1)) if ms else 12.0
        ma = re.search(r'text-anchor="(\w+)"', attrs)
        anchor = ma.group(1) if ma else 'start'
        mx = re.search(r'\bx="(-?\d+(?:\.\d+)?)"', attrs)
        x = float(mx.group(1)) if mx else 0.0
        est = 0.52 * size * len(txt)
        avail = w - 12 if anchor == 'middle' else w - x - 6
        if est > avail:
            fail('svg/overflow', f'node "{gid}" text "{txt[:40]}" est {js_round(est)}px > {js_round(avail)}px available')

fails_now = [f for f in findings if f[0] == 'FAIL']
if fails_now:
    report()

# ---------- optional render (only after a passing check) ----------
for level, code, msg in findings:
    print(f'{level} {code}: {msg}')
warns = [f for f in findings if f[0] == 'WARN']
print(f'\n0 fail, {len(warns)} warn  ({plan_path} / {svg_path})')
try:
    import cairosvg  # type: ignore
except Exception:
    print('SVG checked. PNG not rendered here; run render-png locally.')
    sys.exit(0)
png_path = Path(svg_path).with_suffix('.png')
try:
    cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), scale=1.3)
    print(f'PNG {png_path} rendered via cairosvg at 1.3x')
except Exception as e:
    print(f'PNG not rendered (cairosvg error: {e}); run render-png locally.', file=sys.stderr)
sys.exit(0)
