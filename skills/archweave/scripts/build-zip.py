#!/usr/bin/env python3
"""Build the ArchWeave skill zip. Python 3.9+, standard library only.

Usage (from the repository root or anywhere):
    python skills/archweave/scripts/build-zip.py                      # dist/archweave-skill.zip
    python skills/archweave/scripts/build-zip.py --target agent-builder
                                                                               # dist/archweave-skill-agent-builder.zip

Both zips put SKILL.md at the zip root with assets/, examples/, references/,
schemas/ and scripts/ beside it.

--target agent-builder produces a package that satisfies the Microsoft 365
Copilot custom-skill upload rules (checked against the Microsoft docs on
2026-10-22): only listed file types, zip under 50 MB, files under 25 MB,
at most 350 files, directory depth at most 3. For that target:
  * only SKILL.md, scripts/, references/ and assets/ are used. Agent Builder rejects .json outside
    resource folders ("File type '.json' is not supported for skill script files"), so:
      schemas/<x>.schema.json          -> references/schemas/<x>.schema.json
      examples/<name>/plan.json        -> assets/examples/<name>-plan.json
      examples/<name>/<slug>.svg       -> assets/examples/<name>.xml   (same bytes, renamed)
    and every .md in the package has its schemas/ and examples/ paths rewritten to match,
  * scripts/render-png.*, scripts/build-zip.py, scripts/test-checker.py and examples/*/*.png are left out
    (the first two work only inside the repository, the last is dead weight here),
  * files under scripts/ must be script types; .json, .xml and .png may sit only under references/ or assets/,
  * every remaining entry's extension is asserted against Microsoft's list.
"""
import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent          # skills/archweave
REPO = SKILL.parent.parent                              # repository root
DIST = REPO / 'dist'

# From https://learn.microsoft.com/microsoft-365/copilot/extensibility/declarative-agent-skills
# "Supported file and script types", as of 2026-09-03.
M365_ALLOWED = {
    '.json', '.xml', '.yaml', '.yml', '.ini', '.config', '.utf8', '.docx', '.doc', '.docm', '.pdf',
    '.txt', '.rtf', '.md', '.ppt', '.pptx', '.ppsm', '.xlsx', '.xls', '.xlsm', '.csv', '.tsv',
    '.html', '.htm', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.log',
    '.py', '.js', '.mjs', '.cjs', '.ts', '.mts', '.sh', '.bash',
}
# Agent Builder treats every file under scripts/ as a script file; a .json there is rejected
# ("File type '.json' is not supported for skill script files"), although .json is fine elsewhere.
M365_SCRIPT_EXT = {'.py', '.js', '.mjs', '.cjs', '.ts', '.mts', '.sh', '.bash'}
M365_RESOURCE_DIRS = {'references', 'assets'}
M365_MAX_ZIP = 50 * 1024 * 1024
M365_MAX_FILE = 25 * 1024 * 1024
M365_MAX_FILES = 350
M365_MAX_DEPTH = 3          # counted as path components including the file name, from the zip root


ALLOWED_TOP = {'SKILL.md', 'assets', 'examples', 'references', 'schemas', 'scripts'}


def rewrite_paths(text):
    """Point schemas/ and examples/ mentions at the Agent Builder layout."""
    text = re.sub(r'(?<![\w/])schemas/', 'references/schemas/', text)
    text = re.sub(r'(?<![\w/])examples/([a-z0-9-]+)/', r'assets/examples/\1-plan.json and assets/examples/\1.xml', text)
    text = text.replace('Each example folder holds `plan.json` and the finished diagram.', 'Each example is two flat files under `assets/examples/`: `<name>-plan.json` and `<name>.xml`.')
    return text


def entries(target):
    """Yield (source_path, archive_name, transform) for the chosen target.

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
        transform = None
        if target == 'agent-builder':
            if rel.parts[0] == 'scripts' and (rel.name.startswith('render-png.') or rel.name in ('build-zip.py', 'test-checker.py')):
                continue
            if rel.parts[0] == 'examples':
                if rel.suffix == '.png':
                    continue
                name = rel.parts[1]
                if rel.name == 'plan.json':
                    rel = Path('assets/examples') / f'{name}-plan.json'
                elif rel.suffix == '.svg':
                    rel = Path('assets/examples') / f'{name}.xml'
                else:
                    print(f'FAIL {rel.as_posix()}: unexpected file in an example folder', file=sys.stderr)
                    sys.exit(1)
            elif rel.parts[0] == 'schemas':
                rel = Path('references/schemas') / rel.name
            if rel.suffix == '.md':
                transform = rewrite_paths
        yield p, rel.as_posix(), transform


def build(target):
    DIST.mkdir(exist_ok=True)
    name = 'archweave-skill.zip' if target == 'standard' else 'archweave-skill-agent-builder.zip'
    out = DIST / name
    count = 0
    depth = 0
    problems = []
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for src, arc, transform in entries(target):
            size = src.stat().st_size
            parts = arc.split('/')
            depth = max(depth, len(parts))
            if target == 'agent-builder':
                ext = Path(arc).suffix.lower()
                if ext not in M365_ALLOWED:
                    problems.append(f'{arc}: extension {ext or "(none)"} not in Microsoft list')
                if parts[0] == 'scripts' and ext not in M365_SCRIPT_EXT:
                    problems.append(f'{arc}: only script types are allowed under scripts/ ({", ".join(sorted(M365_SCRIPT_EXT))}); move it to references/')
                if ext in ('.json', '.xml', '.png') and parts[0] not in M365_RESOURCE_DIRS:
                    problems.append(f'{arc}: {ext} files may sit only under references/ or assets/ in an Agent Builder package')
                if size > M365_MAX_FILE:
                    problems.append(f'{arc}: {size} bytes exceeds 25 MB')
            if transform:
                z.writestr(arc, transform(src.read_text(encoding='utf-8')))
            else:
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
