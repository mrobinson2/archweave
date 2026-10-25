#!/usr/bin/env python3
"""Inventory the Python runtime this script is running in. Standard library only, Python 3.6+.

Prints a Markdown report to stdout and writes probe-report.md and probe-report.json next to the
script (or to the directory given as the first argument). Nothing is sent anywhere: the one
network test opens a socket and reports whether it was refused.

Sections: interpreter, platform and limits, filesystem (cwd, script dir, writable dirs, file
round-trip), environment variable names (values masked), installed distributions with versions,
importability of packages a diagram or document skill might want, network reachability.
"""
import ctypes.util
import datetime
import importlib
import json
import os
import pkgutil
import platform
import socket
import sys
import time

CANDIDATES = [
    # rendering and images
    'cairosvg', 'cairocffi', 'PIL', 'matplotlib', 'svglib', 'reportlab', 'wand', 'skimage', 'cv2', 'imageio',
    # documents
    'pptx', 'docx', 'openpyxl', 'xlsxwriter', 'fpdf', 'pypdf', 'PyPDF2', 'fitz', 'markdown', 'jinja2',
    # data and science
    'numpy', 'pandas', 'scipy', 'sklearn', 'statsmodels', 'pyarrow', 'polars', 'sympy',
    # graphs and diagrams
    'networkx', 'graphviz', 'pydot', 'plotly', 'seaborn', 'bokeh',
    # parsing and web
    'lxml', 'bs4', 'yaml', 'toml', 'tomllib', 'requests', 'httpx', 'urllib3', 'aiohttp',
    # misc
    'pydantic', 'jsonschema', 'chardet', 'dateutil', 'pytz', 'tzdata', 'cryptography', 'nacl', 'zipfile', 'sqlite3', 'ssl',
]
MASK = ('KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'PASSWD', 'CREDENTIAL', 'AUTH', 'SAS', 'CONNECTIONSTRING', 'COOKIE')


def section(title):
    return '\n## ' + title + '\n'


def distributions():
    out = []
    try:
        import importlib.metadata as im  # 3.8+
        for d in im.distributions():
            name = d.metadata.get('Name') or d.metadata.get('name') or '?'
            out.append((name, d.version or '?'))
    except Exception:
        try:
            import pkg_resources
            for d in pkg_resources.working_set:
                out.append((d.project_name, d.version))
        except Exception:
            for p in sys.path:
                if os.path.isdir(p):
                    for n in os.listdir(p):
                        if n.endswith('.dist-info') or n.endswith('.egg-info'):
                            base = n.rsplit('.', 1)[0]
                            parts = base.split('-', 1)
                            out.append((parts[0], parts[1] if len(parts) > 1 else '?'))
    seen = {}
    for n, v in out:
        seen.setdefault(n.lower(), (n, v))
    return sorted(seen.values(), key=lambda t: t[0].lower())


def try_import(name):
    t = time.time()
    try:
        m = importlib.import_module(name)
        ver = getattr(m, '__version__', None) or getattr(m, 'VERSION', None) or ''
        return True, str(ver), round(time.time() - t, 3)
    except Exception as e:
        return False, type(e).__name__ + ': ' + str(e)[:80], round(time.time() - t, 3)


def writable(path):
    try:
        test = os.path.join(path, '.probe-write-test')
        with open(test, 'w') as f:
            f.write('ok')
        os.remove(test)
        return True
    except Exception:
        return False


def toplevel_modules():
    """Top-level importable names in every non-stdlib sys.path entry (finds packages that have no dist-info)."""
    std = os.path.dirname(os.__file__)
    skip = {os.path.abspath(std), os.path.abspath(os.path.join(std, 'lib-dynload'))}
    here = os.path.dirname(os.path.abspath(__file__))
    out = {}
    for p in sys.path:
        if not p or not os.path.isdir(p) or os.path.abspath(p) in skip or os.path.abspath(p) == here:
            continue
        try:
            names = sorted({m.name for m in pkgutil.iter_modules([p]) if not m.name.startswith('_')})
        except Exception as e:
            names = ['(unreadable: %s)' % type(e).__name__]
        out[p] = names
    return out


def network():
    results = []
    for host, port in (('1.1.1.1', 443), ('pypi.org', 443), ('login.microsoftonline.com', 443)):
        t = time.time()
        try:
            s = socket.create_connection((host, port), timeout=3)
            s.close()
            results.append((host, port, 'CONNECTED', round(time.time() - t, 2)))
        except Exception as e:
            results.append((host, port, 'blocked: ' + type(e).__name__, round(time.time() - t, 2)))
    try:
        socket.gethostbyname('pypi.org')
        dns = 'resolves'
    except Exception as e:
        dns = 'fails: ' + type(e).__name__
    return results, dns


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    started = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    report = {'generated_utc': started}
    md = ['# Python runtime probe', '', 'Generated ' + started + ' UTC. Values are what this interpreter reports; nothing was sent anywhere.']

    md.append(section('Interpreter'))
    report['interpreter'] = {'version': sys.version.replace('\n', ' '), 'executable': sys.executable, 'implementation': platform.python_implementation(),
                             'prefix': sys.prefix, 'base_prefix': getattr(sys, 'base_prefix', ''), 'venv': sys.prefix != getattr(sys, 'base_prefix', sys.prefix)}
    for k, v in report['interpreter'].items():
        md.append('- %s: `%s`' % (k, v))

    md.append(section('Platform and limits'))
    lim = {'platform': platform.platform(), 'machine': platform.machine(), 'cpu_count': os.cpu_count(), 'user': os.environ.get('USER') or os.environ.get('USERNAME') or '?',
           'pid': os.getpid(), 'uid': getattr(os, 'getuid', lambda: 'n/a')()}
    try:
        import resource
        for name in ('RLIMIT_AS', 'RLIMIT_CPU', 'RLIMIT_NOFILE', 'RLIMIT_FSIZE', 'RLIMIT_NPROC'):
            if hasattr(resource, name):
                soft, hard = resource.getrlimit(getattr(resource, name))
                lim[name] = '%s / %s' % ('unlimited' if soft == -1 else soft, 'unlimited' if hard == -1 else hard)
    except Exception as e:
        lim['rlimits'] = 'unavailable: ' + type(e).__name__
    try:
        with open('/proc/meminfo') as f:
            lim['MemTotal'] = f.readline().strip()
    except Exception:
        pass
    report['limits'] = lim
    for k, v in lim.items():
        md.append('- %s: `%s`' % (k, v))

    md.append(section('Filesystem'))
    here = os.path.dirname(os.path.abspath(__file__))
    fs = {'cwd': os.getcwd(), 'script_dir': here, 'home': os.path.expanduser('~'), 'tmp': __import__('tempfile').gettempdir()}
    fs['writable'] = {p: writable(p) for p in sorted({fs['cwd'], here, fs['home'], fs['tmp'], out_dir}) if os.path.isdir(p)}
    try:
        fs['cwd_listing'] = sorted(os.listdir(os.getcwd()))[:60]
        fs['script_dir_listing'] = sorted(os.listdir(here))[:60]
        parent = os.path.dirname(here)
        fs['skill_root_listing'] = sorted(os.listdir(parent))[:60]
    except Exception as e:
        fs['listing_error'] = type(e).__name__
    try:
        total, used, free = __import__('shutil').disk_usage(os.getcwd())
        fs['disk_free_mb'] = free // (1024 * 1024)
    except Exception:
        pass
    report['filesystem'] = fs
    for k, v in fs.items():
        md.append('- %s: `%s`' % (k, json.dumps(v) if isinstance(v, (dict, list)) else v))

    md.append(section('Environment variable names (values masked)'))
    env = {}
    for k in sorted(os.environ):
        v = os.environ[k]
        env[k] = '***' if any(m in k.upper() for m in MASK) else (v if len(v) <= 60 else v[:57] + '...')
    report['environment'] = env
    md.append('`' + ', '.join(sorted(env)) + '`')
    md.append('')
    md.append('Unmasked short values: ' + ', '.join('%s=%s' % (k, v) for k, v in env.items() if v != '***' and len(v) <= 30)[:1500])

    md.append(section('Installed distributions'))
    dists = distributions()
    report['distributions'] = [{'name': n, 'version': v} for n, v in dists]
    md.append('%d distributions found.' % len(dists))
    md.append('')
    md.append('| Package | Version |')
    md.append('|---|---|')
    for n, v in dists:
        md.append('| %s | %s |' % (n, v))

    md.append(section('Import test for packages a diagram or document skill might want'))
    imp = {}
    md.append('| Module | Importable | Version or error | Seconds |')
    md.append('|---|---|---|---|')
    for name in CANDIDATES:
        ok, info, secs = try_import(name)
        imp[name] = {'ok': ok, 'info': info, 'seconds': secs}
        md.append('| %s | %s | %s | %s |' % (name, 'yes' if ok else 'no', info, secs))
    report['imports'] = imp

    md.append(section('Network'))
    results, dns = network()
    report['network'] = {'dns_pypi': dns, 'connections': [{'host': h, 'port': p, 'result': r, 'seconds': s} for h, p, r, s in results]}
    md.append('- DNS for pypi.org: ' + dns)
    for h, p, r, s in results:
        md.append('- %s:%s: %s (%ss)' % (h, p, r, s))

    md.append(section('Module search path'))
    report['sys_path'] = sys.path
    for p in sys.path:
        md.append('- `%s`' % p)

    md.append(section('Top-level modules per package folder (every non-stdlib sys.path entry)'))
    tops = toplevel_modules()
    report['toplevel_modules'] = tops
    for path, names in tops.items():
        md.append('### `%s` (%d)' % (path, len(names)))
        md.append(', '.join(names) if names else '(none)')
        md.append('')

    yes = [n for n in CANDIDATES if imp[n]['ok']]
    no = [n for n in CANDIDATES if not imp[n]['ok']]
    cairo_lib = ctypes.util.find_library('cairo')
    total_top = len({n for names in tops.values() for n in names})
    connected = [h for h, p, r, s in results if r == 'CONNECTED']
    summary = [
        '', '## SUMMARY (copy this block first; the full tables follow)', '',
        '- Python: `%s` at `%s` (venv: %s)' % (sys.version.split()[0], sys.executable, report['interpreter']['venv']),
        '- Importable (%d of %d tested): %s' % (len(yes), len(CANDIDATES), ', '.join(yes) or 'none'),
        '- NOT importable (%d): %s' % (len(no), ', '.join(no) or 'none'),
        '- cairosvg importable: %s; system libcairo found: %s' % ('yes' if imp.get('cairosvg', {}).get('ok') else 'no', cairo_lib or 'no'),
        '- Installed distributions: %d; top-level modules outside the stdlib: %d' % (len(dists), total_top),
        '- Network: %s' % ('CONNECTED to ' + ', '.join(connected) if connected else 'blocked (no connection succeeded)'),
        '- Writable: %s' % (', '.join(k for k, v in fs['writable'].items() if v) or 'nothing'),
        '- Full data: probe-report.md and probe-report.json in the directory named at the end of this output',
        '',
    ]
    report['summary'] = summary
    md[3:3] = summary

    text = '\n'.join(md) + '\n'
    print(text)
    written = []
    for name, payload in (('probe-report.md', text), ('probe-report.json', json.dumps(report, indent=2, default=str))):
        try:
            path = os.path.join(out_dir, name)
            with open(path, 'w') as f:
                f.write(payload)
            written.append(path)
        except Exception as e:
            print('could not write %s: %s' % (name, e))
    if written:
        print('Report files: ' + ', '.join(written))


if __name__ == '__main__':
    main()
