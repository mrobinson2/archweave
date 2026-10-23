#!/usr/bin/env node
// ArchWeave diagram checker v0.1. Zero dependencies. Node 18+.
// Usage: node check-diagram.mjs <plan.json> <diagram.svg>
// Exit 0 only when every check passes. Prints one line per finding.
//
// Checks:
//   plan: parses, schema_version/diagram_type, meta stamp fields, unique ids,
//         edge endpoints exist, zone parents exist, lane/stage/zone refs exist,
//         label length budgets, lifecycle main_path refers to states.
//   svg:  well-formed enough (balanced root), width/height/viewBox, <title>,
//         no script/animate/foreignObject/external href/http(s),
//         every plan node present as data-node, every zone as data-zone,
//         every edge as data-edge (architecture/dataflow/workflow/lifecycle),
//         every sequence participant as data-node, message as data-edge,
//         data-meta stamp containing pattern_id, date, meta.classification and v<version> when set,
//         text overflow heuristic for node labels/sublabels inside data-node groups,
//         fonts not smaller than 11px, SVG elements not in plan (data-node unknown).

import { readFileSync } from 'node:fs';

const [,, planPath, svgPath] = process.argv;
if (!planPath || !svgPath) {
  console.error('usage: check-diagram.mjs <plan.json> <diagram.svg>');
  process.exit(2);
}

const findings = [];
const fail = (code, msg) => findings.push({ level: 'FAIL', code, msg });
const warn = (code, msg) => findings.push({ level: 'WARN', code, msg });

// ---------- plan ----------
let plan;
try {
  plan = JSON.parse(readFileSync(planPath, 'utf8'));
} catch (e) {
  fail('plan/parse', `cannot parse ${planPath}: ${e.message}`);
  report();
}

const TYPES = ['architecture', 'sequence', 'workflow', 'dataflow', 'lifecycle'];
if (plan.schema_version !== 1) fail('plan/schema-version', 'schema_version must be 1');
if (!TYPES.includes(plan.diagram_type)) fail('plan/type', `diagram_type must be one of ${TYPES.join(', ')}`);
const type = plan.diagram_type;

const meta = plan.meta || {};
for (const k of ['title', 'pattern_id', 'date', 'classification', 'output']) {
  if (!meta[k]) fail('plan/meta', `meta.${k} missing`);
}
if (meta.pattern_id && !/^[a-z0-9]+(-[a-z0-9]+)*$/.test(meta.pattern_id)) {
  fail('plan/meta', `meta.pattern_id "${meta.pattern_id}" must be kebab-case (letters, digits, single hyphens)`);
}
if (meta.version !== undefined && !/^[0-9]+(\.[0-9]+){0,2}$/.test(String(meta.version))) {
  fail('plan/meta', `meta.version "${meta.version}" must look like 1.0`);
}
if (meta.date && !/^20[0-9]{2}-[0-9]{2}-[0-9]{2}$/.test(meta.date)) fail('plan/meta', 'meta.date must be YYYY-MM-DD');
if (meta.classification && !meta.classification.trim()) fail('plan/meta', 'meta.classification must not be blank');

const ID = /^[a-z][a-z0-9-]*$/;
const ids = new Map();
function collect(list, kind) {
  for (const item of list || []) {
    if (!item || typeof item.id !== 'string') { fail(`plan/${kind}`, `${kind} item without id`); continue; }
    if (!ID.test(item.id)) fail(`plan/${kind}`, `${kind} id "${item.id}" must be lowercase kebab`);
    if (ids.has(item.id)) fail('plan/id', `duplicate id "${item.id}" (${ids.get(item.id)} and ${kind})`);
    ids.set(item.id, kind);
  }
}

const nodeKind = { architecture: 'nodes', sequence: 'participants', workflow: 'nodes', dataflow: 'nodes', lifecycle: 'states' }[type];
const edgeKind = { architecture: 'edges', sequence: 'messages', workflow: 'edges', dataflow: 'flows', lifecycle: 'transitions' }[type];
const containerKind = { architecture: 'zones', sequence: null, workflow: 'lanes', dataflow: 'stages', lifecycle: null }[type];

collect(plan[containerKind], containerKind);
collect(plan[nodeKind], nodeKind);
collect(plan[edgeKind], edgeKind);
collect(plan.notes, 'notes');
collect(plan.groups, 'groups');

const nodes = plan[nodeKind] || [];
const edges = plan[edgeKind] || [];
const containers = containerKind ? (plan[containerKind] || []) : [];
const nodeIds = new Set(nodes.map(n => n.id));
const containerIds = new Set(containers.map(c => c.id));

if (nodes.length < 2) fail(`plan/${nodeKind}`, `need at least 2 ${nodeKind}`);
if (edges.length < 1) fail(`plan/${edgeKind}`, `need at least 1 ${edgeKind}`);

const refKey = { architecture: 'zone', workflow: 'lane', dataflow: 'stage' }[type];
for (const n of nodes) {
  if (!n.label) fail('plan/label', `${n.id} has no label`);
  if (n.label && n.label.length > 60) fail('plan/label', `${n.id} label longer than 60 chars`);
  if (n.sublabel && n.sublabel.length > 70) fail('plan/label', `${n.id} sublabel longer than 70 chars`);
  if (refKey && !containerIds.has(n[refKey])) fail('plan/ref', `${n.id}.${refKey} "${n[refKey]}" is not a ${containerKind} id`);
  if (type === 'architecture') {
    for (const k of ['color', 'icon', 'owner']) if (!n[k]) fail('plan/node', `${n.id}.${k} missing`);
    if (n.icon && !/^i-[a-z0-9]+$/.test(n.icon)) fail('plan/node', `${n.id}.icon "${n.icon}" must be i-<name>`);
  }
}
for (const c of containers) {
  if (c.parent && !containerIds.has(c.parent)) fail('plan/ref', `${containerKind} ${c.id}.parent "${c.parent}" unknown`);
}
for (const e of edges) {
  if (!nodeIds.has(e.from)) fail('plan/ref', `${e.id}.from "${e.from}" is not a ${nodeKind} id`);
  if (!nodeIds.has(e.to)) fail('plan/ref', `${e.id}.to "${e.to}" is not a ${nodeKind} id`);
  if (e.from === e.to && type !== 'lifecycle') fail('plan/edge', `${e.id} is a self-loop`);
  if (e.label && e.label.length > 70) fail('plan/label', `${e.id} label longer than 70 chars`);
  if ((type === 'dataflow' || type === 'lifecycle') && !e.label) fail('plan/label', `${e.id} needs a label in ${type}`);
}
if (type === 'lifecycle') {
  for (const s of plan.main_path || []) if (!nodeIds.has(s)) fail('plan/ref', `main_path "${s}" is not a state id`);
}
if (type === 'sequence') {
  for (const g of plan.groups || []) {
    const mids = new Set(edges.map(m => m.id));
    if (!mids.has(g.from_message)) fail('plan/ref', `group ${g.id}.from_message unknown`);
    if (!mids.has(g.to_message)) fail('plan/ref', `group ${g.id}.to_message unknown`);
  }
}
if ((type === 'architecture' || type === 'dataflow') && !plan.legend) fail('plan/legend', `${type} requires legend`);

// orphan nodes
const touched = new Set();
for (const e of edges) { touched.add(e.from); touched.add(e.to); }
for (const n of nodes) if (!touched.has(n.id)) warn('plan/orphan', `${n.id} has no ${edgeKind}`);

// ---------- svg ----------
let svg;
try {
  svg = readFileSync(svgPath, 'utf8');
} catch (e) {
  fail('svg/read', `cannot read ${svgPath}: ${e.message}`);
  report();
}

if (!/^\s*(<\?xml[^>]*\?>\s*)?(<!--[\s\S]*?-->\s*)*<svg[\s>]/.test(svg)) fail('svg/root', 'file must start with <svg');
if (!/<\/svg>\s*$/.test(svg)) fail('svg/root', 'file must end with </svg>');
const rootTag = (svg.match(/<svg[^>]*>/) || [''])[0];
if (!/\bwidth="\d+(\.\d+)?"/.test(rootTag) || !/\bheight="\d+(\.\d+)?"/.test(rootTag)) fail('svg/size', '<svg> needs numeric width and height');
if (!/\bviewBox="/.test(rootTag)) fail('svg/size', '<svg> needs viewBox');
if (!/<title>[^<]+<\/title>/.test(svg)) fail('svg/title', 'missing <title>');

for (const [re, code, msg] of [
  [/<script[\s>]/i, 'svg/forbidden', '<script> not allowed'],
  [/<animate/i, 'svg/forbidden', '<animate*> not allowed'],
  [/<foreignObject/i, 'svg/forbidden', '<foreignObject> not allowed'],
  [/https?:\/\/(?!www\.w3\.org\/)/i, 'svg/external', 'external http(s) reference found (only w3.org namespaces allowed)'],
  [/@import|@font-face/i, 'svg/external', '@import or @font-face not allowed'],
  [/<image[^>]*href="(?!data:)/i, 'svg/external', '<image> must be inline data: or absent'],
]) if (re.test(svg)) fail(code, msg);

// tag balance (rough)
const opens = (svg.match(/<g[\s>]/g) || []).length;
const closes = (svg.match(/<\/g>/g) || []).length;
if (opens !== closes) fail('svg/balance', `<g> open/close mismatch ${opens}/${closes}`);

// plan <-> svg coverage
const attrSet = (attr) => new Set([...svg.matchAll(new RegExp(`${attr}="([^"]+)"`, 'g'))].map(m => m[1]));
const svgNodes = attrSet('data-node');
const svgEdges = attrSet('data-edge');
const svgZones = attrSet('data-zone');

for (const n of nodes) if (!svgNodes.has(n.id)) fail('svg/missing-node', `plan ${nodeKind} "${n.id}" has no data-node in SVG`);
for (const e of edges) if (!svgEdges.has(e.id)) fail('svg/missing-edge', `plan ${edgeKind} "${e.id}" has no data-edge in SVG`);
if (type === 'architecture') for (const z of containers) if (!svgZones.has(z.id)) fail('svg/missing-zone', `plan zone "${z.id}" has no data-zone in SVG`);
if (type === 'workflow' || type === 'dataflow') for (const z of containers) if (!svgZones.has(z.id)) fail('svg/missing-zone', `plan ${containerKind} "${z.id}" has no data-zone in SVG`);
for (const id of svgNodes) if (!nodeIds.has(id)) fail('svg/unknown-node', `SVG data-node "${id}" not in plan`);
for (const id of svgEdges) if (!edges.some(e => e.id === id)) fail('svg/unknown-edge', `SVG data-edge "${id}" not in plan`);

// metadata stamp
const metaBlock = (svg.match(/<g[^>]*data-meta="true"[^>]*>[\s\S]*?<\/g>/) || [''])[0];
if (!metaBlock) fail('svg/meta', 'missing <g data-meta="true"> stamp');
else {
  if (!metaBlock.includes(meta.pattern_id)) fail('svg/meta', `stamp lacks pattern id ${meta.pattern_id}`);
  if (!metaBlock.includes(meta.date)) fail('svg/meta', `stamp lacks date ${meta.date}`);
  if (meta.version && !metaBlock.includes(`v${meta.version}`)) fail('svg/meta', `stamp lacks version v${meta.version}`);
  if (meta.classification && !metaBlock.includes(meta.classification)) fail('svg/meta', `stamp lacks classification "${meta.classification}"`);
}

// body without <defs> (symbols may carry their own font sizes and rects)
const body = svg.replace(/<defs>[\s\S]*?<\/defs>/g, '');

// font floor
for (const m of body.matchAll(/font-size="(\d+(?:\.\d+)?)"/g)) {
  if (parseFloat(m[1]) < 11) { fail('svg/font', `font-size ${m[1]} below 11px floor`); break; }
}

// text overflow heuristic inside data-node groups:
// group's first <rect width=W>, each <text font-size=S text-anchor=middle>: 0.55*S*len must be <= W-12
const groupRe = /<g[^>]*data-node="([^"]+)"[^>]*>([\s\S]*?)<\/g>/g;
for (const m of body.matchAll(groupRe)) {
  const [, id, group] = m;
  const w = parseFloat((group.match(/<rect[^>]*?(?<![-\w])width="(\d+(?:\.\d+)?)"/) || [])[1]);
  if (!w) continue;
  for (const t of group.matchAll(/<text([^>]*)>([^<]*)<\/text>/g)) {
    const attrs = t[1]; const txt = t[2].replace(/&amp;/g, '&').replace(/&[a-z]+;/g, 'x');
    const size = parseFloat((attrs.match(/font-size="(\d+(?:\.\d+)?)"/) || [])[1] || 12);
    const anchor = (attrs.match(/text-anchor="(\w+)"/) || [])[1] || 'start';
    const x = parseFloat((attrs.match(/\bx="(-?\d+(?:\.\d+)?)"/) || [])[1] || 0);
    const est = 0.52 * size * txt.length;
    const avail = anchor === 'middle' ? w - 12 : w - x - 6;
    if (est > avail) fail('svg/overflow', `node "${id}" text "${txt.slice(0, 40)}" est ${Math.round(est)}px > ${Math.round(avail)}px available`);
  }
}

report();

function report() {
  const fails = findings.filter(f => f.level === 'FAIL');
  const warns = findings.filter(f => f.level === 'WARN');
  for (const f of findings) console.log(`${f.level} ${f.code}: ${f.msg}`);
  console.log(`\n${fails.length} fail, ${warns.length} warn  (${planPath} / ${svgPath})`);
  process.exit(fails.length ? 1 : 0);
}
