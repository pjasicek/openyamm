#!/usr/bin/env python3
"""Print a package's model list with the ledger's problems and projects (for the package agent's prompt).
    python3 level_generation/creatures/gait_rollout_20261031/brief.py <package id>"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ledger = json.loads((HERE / "ledger.json").read_text())
for key in json.loads((HERE / "packages.json").read_text())[sys.argv[1]]:
    e = ledger[key]
    projects = [p for p in e["projects"] if not p.startswith(("lod_repair", "head_bob", "gait_rollout"))]
    print(f"- {key} (source assets_source/{e['model']}; {e['body']}; authored walk {e['walk']} run {e['run']}"
          f"{' sprint ' + str(e['sprint']) if e['sprint'] else ''}; projects: {', '.join(projects) or 'none'})")
    for problem in e["problems"]:
        print(f"    {problem}")
