---
name: sandbox-probe
description: "Inventory the Python runtime available to this agent: interpreter version, installed packages, importable libraries, writable paths, network reachability, resource limits. Use when asked what Python, packages, libraries or modules are available, whether a package such as cairosvg or pandas can be imported, whether scripts can write files or reach the network, or to probe, inspect or report on the sandbox or execution environment. Produces a Markdown report and a JSON file."
license: MIT
metadata:
  version: "1.1.0"
  homepage: https://github.com/mrobinson2/archweave
---

# Sandbox probe

One script, standard library only, no network sends. It reports what this Python runtime can do so a skill author knows what to depend on.

## When asked to probe, inspect or list the environment

1. Run, from the skill folder:
   ```bash
   python scripts/probe.py
   ```
   If `python` is not found, try `python3`. If the script directory is not writable, pass a writable directory as the first argument, for example `python scripts/probe.py /tmp`.
2. The output is long on purpose. Reply in this order, without filtering anything:
   a. The **SUMMARY block** at the top of the output, verbatim.
   b. The path of `probe-report.md` and `probe-report.json`, and attach both if the host allows it. If it cannot attach files, say so in one line.
   c. The sections **Installed distributions**, **Import test** and **Top-level modules** exactly as printed. Do not drop rows, drop columns, drop the "no" rows, reorder, or shorten. If the reply would be too long for one message, split it across messages in order and say "part 1 of N"; never omit a part.
3. After that, add at most three lines of your own: Python version, whether `cairosvg` imported, and whether any network connection succeeded.

## When asked whether one specific package is available

Run `python -c "import <name>; print(getattr(<name>, '__version__', 'present'))"` and reply with the exact output or the exact exception text. Never guess from memory; the runtime decides.

## Rules

- Never install, upgrade or download anything. The probe only reads.
- Never print environment variable values that look like secrets. The script masks names containing KEY, TOKEN, SECRET, PASSWORD, CREDENTIAL, AUTH, SAS, COOKIE; keep it that way.
- If the script fails before producing output, reply with the full traceback verbatim, plus the output of `python --version` and `python -c "import sys; print(sys.executable, sys.path)"`.
