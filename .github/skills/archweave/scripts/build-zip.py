#!/usr/bin/env python3
"""Build the ArchWeave skill zip. Python 3.9+, standard library only.

Usage (from the repository root or anywhere):
    python .github/skills/archweave/scripts/build-zip.py                      # dist/archweave-skill.zip
    python .github/skills/archweave/scripts/build-zip.py --target agent-builder
                                                                               # dist/archweave-skill-agent-builder.zip

Both zips put SKILL.md at the zip root with assets/, examples/, references/,
schemas/ and scripts/ beside it.

--target agent-builder produces a package that satisfies the Microsoft 365
Copilot custom-skill upload rules (checked against the Microsoft docs on
2026-10-22): only listed file types, zip under 50 MB, files under 25 MB,
at most 350 files, directory depth at most 3. For that target:
  * examples/*/<slug>.svg are stored as <slug>.xml (same bytes),
  * scripts/render-png.ps1 and scripts/render-png.sh are left out,
  * examples/*/<slug>.png are left out,
  * every remaining entry's extension is asserted against Microsoft's list.
"""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent          # .github/skills/archweave
REPO = SKILL.parent.parent.parent                       # repository root
DIST = REPO / 'dist'

# From https://learn.microsoft.com/microsoft-365/copilot/extensibility/declarative-agent-skills
# "Supported file and script types", as of 2026-09-03.
M365_ALLOWED = {
    '.json', '.xml', '.yaml', '.yml', '.ini', '.config', '.utf8', '.docx', '.doc', '.docm', '.pdf',
    '.txt', '.rtf', '.md', '.ppt', '.pptx', '.ppsm', '.xlsx', '.xls', '.xlsm', '.csv', '.tsv',
    '.html', '.htm', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.log',
    '.py', '.js', '.mjs', '.cjs', '.ts', '.mts', '.sh', '.bash',
}
M365_MAX_ZIP = 50 * 1024 * 1024
M365_MAX_FILE = 25 * 1024 * 1024
M365_MAX_FILES = 350
M365_MAX_DEPTH = 3          # counted as path components including the file name, from the zip root


ALLOWED_TOP = {'SKILL.md', 'assets', 'examples', 'references', 'schemas', 'scripts'}


def entries(target):
    """Yield (source_path, archive_name) pairs for the chosen target.

    Only SKILL.md and the five known folders ship; anything else under the skill
    folder is reported and refused, so a stray file cannot end up in a public zip.
    """
    for p in sorted(SKILL.rglob('*')):
        if p.is_dir() or '__pycache__' in p.parts or p.name == '.DS_Store':
            continue
        rel = p.relative_to(SKILL)
        if rel.parts[0] not in ALLOWED_TOP:
            print(f'FAIL {rel.as_posix()}: not in the allowed top-level set {sorted(ALLOWED_TOP)}', file=sys.stderr)
            sys.exit(1)
        if target == 'agent-builder':
            if rel.parts[0] == 'scripts' and rel.name.startswith('render-png.'):
                continue
            if rel.parts[0] == 'examples' and rel.suffix == '.png':
                continue
            if rel.parts[0] == 'examples' and rel.suffix == '.svg':
                rel = rel.with_suffix('.xml')
        yield p, rel.as_posix()


def build(target):
    DIST.mkdir(exist_ok=True)
    name = 'archweave-skill.zip' if target == 'standard' else 'archweave-skill-agent-builder.zip'
    out = DIST / name
    count = 0
    depth = 0
    problems = []
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for src, arc in entries(target):
            size = src.stat().st_size
            parts = arc.split('/')
            depth = max(depth, len(parts))
            if target == 'agent-builder':
                ext = Path(arc).suffix.lower()
                if ext not in M365_ALLOWED:
                    problems.append(f'{arc}: extension {ext or "(none)"} not in Microsoft list')
                if size > M365_MAX_FILE:
                    problems.append(f'{arc}: {size} bytes exceeds 25 MB')
            z.write(src, arc)
            count += 1
    if target == 'agent-builder':
        if count > M365_MAX_FILES:
            problems.append(f'{count} files exceeds {M365_MAX_FILES}')
        if depth > M365_MAX_DEPTH:
            problems.append(f'path depth {depth} exceeds {M365_MAX_DEPTH}')
        if out.stat().st_size > M365_MAX_ZIP:
            problems.append('zip exceeds 50 MB')
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
    if 'SKILL.md' not in names:
        problems.append('SKILL.md missing from zip root')
    if problems:
        out.unlink()
        for p in problems:
            print('FAIL', p, file=sys.stderr)
        sys.exit(1)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    (DIST / (name + '.sha256')).write_text(f'{digest}  {name}\n')
    print(f'{out.relative_to(REPO)}  {count} files  depth {depth}  {out.stat().st_size / 1e6:.2f} MB')
    print(f'SHA-256 {digest}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--target', choices=['standard', 'agent-builder'], default='standard')
    args = ap.parse_args()
    build(args.target)
