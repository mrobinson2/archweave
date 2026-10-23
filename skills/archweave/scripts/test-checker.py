#!/usr/bin/env python3
"""Hostile-input tests for check-diagram.py. Python 3.9+, standard library only.

Usage: python scripts/test-checker.py        (run from the skill folder)
Takes the sequence example, injects one hostile fragment per case, and asserts the
checker exits 1 with the expected code. Also asserts every shipped example still passes.
Exit 0 only when all cases behave.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CHECK = SKILL / 'scripts' / 'check-diagram.py'
EX = SKILL / 'examples'


def run(plan, svg):
    p = subprocess.run([sys.executable, str(CHECK), str(plan), str(svg)], capture_output=True, text=True)
    return p.returncode, p.stdout


def main():
    seq = EX / 'sequence-api-request'
    plan = seq / 'plan.json'
    base = next(p for p in seq.iterdir() if p.suffix in ('.svg', '.xml')).read_text(encoding='utf-8')
    anchor = '<rect width="100%" height="100%" fill="#FFFFFF"/>'
    inject = lambda frag: base.replace(anchor, frag + '\n  ' + anchor, 1)
    cases = {
        'use-file-href': (inject('<use href="file:///etc/passwd"/>'), 'svg/external'),
        'use-protocol-relative': (inject('<use href="//evil.example/x.svg#a"/>'), 'svg/external'),
        'use-relative-path': (inject('<use href="../../secret.svg#a"/>'), 'svg/external'),
        'xlink-href-file': (inject('<use xlink:href="file:///etc/hosts"/>'), 'svg/external'),
        'image-file': (inject('<image href="file:///etc/hosts" width="10" height="10"/>'), 'svg/external'),
        'image-http-upper': (inject('<image href="HTTP://evil.example/a.png" width="10" height="10"/>'), 'svg/external'),
        'style-url-file': (inject('<style>rect{fill:url(file:///x.svg#p)}</style>'), 'svg/external'),
        'feImage-file': (inject('<filter id="f"><feImage href="file:///etc/hosts"/></filter>'), 'svg/external'),
        'doctype-entity': (base.replace('<svg ', '<!DOCTYPE svg [<!ENTITY a "aaaa">]>\n<svg ', 1), 'svg/forbidden'),
        'script-upper': (inject('<SCRIPT>alert(1)</SCRIPT>'), 'svg/forbidden'),
        'onload-handler': (base.replace('<svg ', '<svg onload="alert(1)" ', 1), 'svg/forbidden'),
        'onclick-text': (inject('<text onclick="alert(1)">x</text>'), 'svg/forbidden'),
        'javascript-href': (inject('<a href="javascript:alert(1)"><rect width="1" height="1"/></a>'), 'svg/forbidden'),
        'set-element': (inject('<set attributeName="x" to="1"/>'), 'svg/forbidden'),
        'animate-element': (inject('<animate attributeName="x" to="1"/>'), 'svg/forbidden'),
        'foreign-object': (inject('<foreignObject><div/></foreignObject>'), 'svg/forbidden'),
        'css-import-space': (inject('<style>@ import url(x)</style>'), 'svg/external'),
        'font-face': (inject('<style>@font-face{src:url(x)}</style>'), 'svg/external'),
    }
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        for name, (svg, code) in cases.items():
            f = Path(td) / f'{name}.svg'
            f.write_text(svg, encoding='utf-8')
            rc, out = run(plan, f)
            ok = rc == 1 and re.search(rf'^FAIL {re.escape(code)}:', out, re.M)
            print(f'{"ok  " if ok else "BAD "}{name:24} exit={rc}')
            bad += 0 if ok else 1
    for d in sorted(EX.iterdir()):
        if not d.is_dir():
            continue
        diagram = next(p for p in d.iterdir() if p.suffix in ('.svg', '.xml'))
        rc, out = run(d / 'plan.json', diagram)
        ok = rc == 0 and '0 fail' in out
        print(f'{"ok  " if ok else "BAD "}example {d.name:28} exit={rc}')
        bad += 0 if ok else 1
    print(f'\n{bad} failing case(s)')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
