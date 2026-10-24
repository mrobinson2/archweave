#!/usr/bin/env python3
"""Fill the platform rows of references/vocabulary.md from an Azure Resource Graph export.
Python 3.9+, standard library only. No network: you run the query, export, and feed the file in.

Why: the vocabulary is where hub ranges, subnets, the shared APIM, the egress firewall, DNS zones and
the log workspace are named. Typing them by hand is how wrong facts reach a diagram. This script
reads what Azure says and writes the rows; a human still adds owners and the "position and default"
sentence, which Azure cannot know.

Step 1, run this query in Azure Resource Graph Explorer (or `az graph query -q "..." -o json`):

    resources
    | where type in~ (
        'microsoft.network/virtualnetworks',
        'microsoft.network/azurefirewalls',
        'microsoft.apimanagement/service',
        'microsoft.network/privatednszones',
        'microsoft.network/trafficmanagerprofiles',
        'microsoft.network/frontdoors',
        'microsoft.cdn/profiles',
        'microsoft.operationalinsights/workspaces',
        'microsoft.eventhub/namespaces')
    | project name, type, location, resourceGroup, subscriptionId, sku, properties

Step 2, export as JSON (the portal's "Download as CSV" also works; the properties column is JSON text).

Step 3:
    python scripts/build-vocabulary.py export.json                       # prints the generated rows
    python scripts/build-vocabulary.py export.json --write rows.md        # writes them to a file
    python scripts/build-vocabulary.py export.json --apply references/vocabulary.md
                                                                          # replaces matching rows in place

--apply matches rows by their first cell ("Hub VNets", "Shared APIM (external)", "Egress firewall",
"Private DNS zones", "DNS steering", "Log Analytics", "Event Hubs") and leaves every other row alone.
Rows the export has no data for are left as they were. Review the diff before committing.

Hub detection: a VNet is a hub if its name contains "hub", or it has an AzureFirewallSubnet, or it has
three or more peerings. Everything else is treated as a spoke and summarized, not listed.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

PLATFORM_ROWS = ['Hub VNets', 'Shared APIM (external)', 'Egress firewall', 'Private DNS zones', 'DNS steering', 'Log Analytics', 'Event Hubs']
TODO = 'Owned by TBD; add the position-and-default sentence'


def load(path):
    text = Path(path).read_text(encoding='utf-8-sig')
    if path.lower().endswith('.csv'):
        rows = list(csv.DictReader(text.splitlines()))
    else:
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get('data') or data.get('value') or data.get('rows') or []
        rows = data
    out = []
    for r in rows:
        r = {str(k).strip().lower(): v for k, v in r.items()}
        props = r.get('properties')
        if isinstance(props, str):
            try:
                props = json.loads(props)
            except Exception:
                props = {}
        sku = r.get('sku')
        if isinstance(sku, str):
            try:
                sku = json.loads(sku)
            except Exception:
                sku = {'name': sku}
        out.append({'name': r.get('name', ''), 'type': str(r.get('type', '')).lower(), 'location': r.get('location', ''),
                    'rg': r.get('resourcegroup', ''), 'props': props or {}, 'sku': sku or {}})
    return out


def subnet_prefix(subnet):
    p = subnet.get('properties', subnet)
    return p.get('addressPrefix') or (p.get('addressPrefixes') or [''])[0]


def analyze(rows):
    vnets = [r for r in rows if r['type'] == 'microsoft.network/virtualnetworks']
    hubs, spokes = [], []
    subnet_index = {}   # subnet resource id (lower) -> (vnet name, subnet name, prefix)
    for v in vnets:
        p = v['props']
        subnets = p.get('subnets') or []
        for s in subnets:
            subnet_index[str(s.get('id', '')).lower()] = (v['name'], s.get('name', ''), subnet_prefix(s))
        names = {s.get('name', '') for s in subnets}
        peerings = len(p.get('virtualNetworkPeerings') or [])
        is_hub = 'hub' in v['name'].lower() or 'AzureFirewallSubnet' in names or peerings >= 3
        entry = {'name': v['name'], 'location': v['location'], 'prefixes': (p.get('addressSpace') or {}).get('addressPrefixes') or [],
                 'subnets': [(s.get('name', ''), subnet_prefix(s)) for s in subnets], 'peerings': peerings}
        (hubs if is_hub else spokes).append(entry)

    def where(subnet_id):
        hit = subnet_index.get(str(subnet_id or '').lower())
        return f'subnet `{hit[2]}` ({hit[1]}) in `{hit[0]}`' if hit else 'subnet TBD'

    result = {'hubs': hubs, 'spokes': spokes}
    apims = [r for r in rows if r['type'] == 'microsoft.apimanagement/service']
    if apims:
        a = apims[0]
        sub_id = ((a['props'].get('virtualNetworkConfiguration') or {}).get('subnetResourceId'))
        result['apim'] = {'name': a['name'], 'sku': a['sku'].get('name', 'TBD'), 'mode': a['props'].get('virtualNetworkType', 'TBD'),
                          'where': where(sub_id), 'extra': len(apims) - 1}
    fws = [r for r in rows if r['type'] == 'microsoft.network/azurefirewalls']
    if fws:
        f = fws[0]
        ipc = (f['props'].get('ipConfigurations') or [{}])[0]
        sub_id = ((ipc.get('properties') or ipc).get('subnet') or {}).get('id')
        tier = (f['props'].get('sku') or {}).get('tier') or f['sku'].get('tier') or 'TBD'
        result['firewall'] = {'name': f['name'], 'tier': tier, 'where': where(sub_id), 'extra': len(fws) - 1}
    zones = [r['name'] for r in rows if r['type'] == 'microsoft.network/privatednszones']
    if zones:
        result['dns_zones'] = sorted(zones)
    tms = [r for r in rows if r['type'] == 'microsoft.network/trafficmanagerprofiles']
    fds = [r for r in rows if r['type'] in ('microsoft.network/frontdoors', 'microsoft.cdn/profiles')]
    if tms:
        t = tms[0]
        result['steering'] = {'kind': 'Azure Traffic Manager', 'name': t['name'], 'fqdn': (t['props'].get('dnsConfig') or {}).get('fqdn', 'TBD'),
                              'method': t['props'].get('trafficRoutingMethod', 'TBD')}
    elif fds:
        result['steering'] = {'kind': 'Azure Front Door', 'name': fds[0]['name'], 'fqdn': 'TBD', 'method': 'n/a'}
    laws = [r for r in rows if r['type'] == 'microsoft.operationalinsights/workspaces']
    if laws:
        ret = sorted({int(r['props'].get('retentionInDays') or 0) for r in laws if r['props'].get('retentionInDays')})
        result['law'] = {'count': len(laws), 'retention': ret}
    ehs = [r for r in rows if r['type'] == 'microsoft.eventhub/namespaces']
    if ehs:
        result['eh'] = {'names': sorted(r['name'] for r in ehs)}
    return result


def rows_markdown(a):
    rows = {}
    if a['hubs']:
        hubs = ', '.join(f"`{h['name']} {' '.join(h['prefixes'])}` ({h['location']}, {len(h['subnets'])} subnets, {h['peerings']} peerings)" for h in a['hubs'])
        rows['Hub VNets'] = f"| Hub VNets | zone | grey | {hubs}. |"
    if a.get('apim'):
        x = a['apim']
        more = f" {x['extra']} further instance(s) in the export." if x['extra'] else ''
        rows['Shared APIM (external)'] = f"| Shared APIM (external) | `i-apim` | grey | `{x['name']}`, {x['sku']}, {x['mode']} mode, {x['where']}. Workload registers APIs and products; does not deploy its own APIM. {TODO}.{more} |"
    if a.get('firewall'):
        x = a['firewall']
        rows['Egress firewall'] = f"| Egress firewall | `i-firewall` | grey | Azure Firewall `{x['name']}` ({x['tier']}) in {x['where']}, all spoke egress and inter-spoke traffic. Rules requested through a change request. {TODO}. |"
    if a.get('dns_zones'):
        z = a['dns_zones']
        shown = ', '.join(f'`{n}`' for n in z[:6]) + (f' and {len(z) - 6} more' if len(z) > 6 else '')
        rows['Private DNS zones'] = f"| Private DNS zones | `i-dns` | grey | Hub owned, {len(z)} zones: {shown}. Linked to every spoke; the workload creates records through private endpoint auto-registration, never zones. |"
    if a.get('steering'):
        x = a['steering']
        rows['DNS steering'] = f"| DNS steering | `i-dns-lb` | orange | {x['kind']} `{x['name']}`, `{x['fqdn']}`, routing {x['method']}, steering to the regional APIM. {TODO}. |"
    if a.get('law'):
        x = a['law']
        ret = ', '.join(f'{d} d' for d in x['retention']) or 'TBD'
        rows['Log Analytics'] = f"| Log Analytics | `i-law` | teal | {x['count']} workspace(s) in the export, retention {ret}. One workspace per workload per environment. {TODO}. |"
    if a.get('eh'):
        x = a['eh']
        rows['Event Hubs'] = f"| Event Hubs | `i-eh` | teal | Platform owned namespace(s) {', '.join(f'`{n}`' for n in x['names'][:3])}, diagnostic settings target, the SIEM data connector reads from here. {TODO}. |"
    return rows


def apply(vocab_path, rows):
    p = Path(vocab_path)
    lines = p.read_text(encoding='utf-8').split('\n')
    replaced = []
    for i, line in enumerate(lines):
        m = re.match(r'\|\s*([^|]+?)\s*\|', line)
        if m and m.group(1) in rows:
            lines[i] = rows[m.group(1)]
            replaced.append(m.group(1))
    missing = [k for k in rows if k not in replaced]
    p.write_text('\n'.join(lines), encoding='utf-8')
    return replaced, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('export', help='Resource Graph export, .json or .csv')
    ap.add_argument('--write', help='write the generated rows to this file')
    ap.add_argument('--apply', help='replace matching rows in this vocabulary.md in place')
    args = ap.parse_args()

    rows_in = load(args.export)
    if not rows_in:
        sys.exit('export has no rows')
    a = analyze(rows_in)
    rows = rows_markdown(a)
    header = (f"<!-- generated by build-vocabulary.py from {Path(args.export).name}: {len(a['hubs'])} hub VNet(s), "
              f"{len(a['spokes'])} spoke VNet(s) summarized, {len(rows)} platform rows. Owners and defaults still need a human. -->")
    out = header + '\n' + '\n'.join(rows[k] for k in PLATFORM_ROWS if k in rows) + '\n'
    if a['spokes']:
        out += f"\n<!-- spokes seen ({len(a['spokes'])}): " + ', '.join(f"{s['name']} {' '.join(s['prefixes'])}" for s in a['spokes'][:12]) + ' -->\n'
    if args.write:
        Path(args.write).write_text(out, encoding='utf-8')
        print(f'wrote {args.write} ({len(rows)} rows)')
    if args.apply:
        replaced, missing = apply(args.apply, rows)
        print(f"applied to {args.apply}: replaced {', '.join(replaced) or 'nothing'}")
        if missing:
            print(f"no matching row in the vocabulary for: {', '.join(missing)} (add them by hand from the output above)")
    if not args.write and not args.apply:
        print(out)
    todo = sum(1 for r in rows.values() if 'TBD' in r)
    print(f'{todo} row(s) still carry TBD or an owner placeholder; fill those before relying on the vocabulary.', file=sys.stderr)


if __name__ == '__main__':
    main()
