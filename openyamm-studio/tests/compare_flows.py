#!/usr/bin/env python3
"""Compares what a map's event handlers test and do before and after an overlay.

  compare_flows.py <base flow.json> <overlay flow.json> <project folder> <label> [--need N]

The two files are `oymap flow <map>` of the shipped map and of the map with the project's overlay in front. Every
handler the project replaces (wiring.yml `replaces`, numbers from ids.lock.yml) must have the same paths: the same
tests with the same answers and the same effects (their order within a path is not compared: opening one door
before closing another is the same handler). No other handler may change. --need N requires at least N replaced
handlers. Exit code 1 on any difference.
"""
import json
import re
import sys


def paths(event):
    return sorted((tuple((t['what'], t['taken']) for t in p['tests']), tuple(sorted(p['effects'])))
                  for p in event['paths'])


def main():
    base, overlay = (dict((e['event'], e) for e in json.load(open(p))) for p in sys.argv[1:3])
    project, label = sys.argv[3], sys.argv[4]
    need = int(sys.argv[sys.argv.index('--need') + 1]) if '--need' in sys.argv else 1
    lock = open(f'{project}/ids.lock.yml').read()
    names = re.findall(r'replaces: "?(evt:\w+)', open(f'{project}/wiring.yml').read())
    replaced = [int(re.search(rf'{re.escape(name)}: (\d+)', lock)[1]) for name in names]
    different = [n for n in replaced if paths(base[n]) != paths(overlay[n])]
    untouched = [n for n in base if n not in replaced and paths(base[n]) != paths(overlay.get(n, {'paths': []}))]
    print(f'{label}: {len(replaced) - len(different)} of {len(replaced)} replaced handlers test and do the same; '
          f'{len(untouched)} other handlers changed')
    for n in different:
        print(f'  event {n} differs:\n    shipped: {paths(base[n])}\n    overlay: {paths(overlay[n])}')
    return 1 if different or untouched or len(replaced) < need else 0


sys.exit(main())
