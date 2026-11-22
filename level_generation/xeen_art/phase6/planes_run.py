#!/usr/bin/env python3
"""Runs the planes' L1 chain for one pair (A6's planes sub-agent, 2026-11-21): render and measure, write the briefs,
`oymap fmt`, `fmt --check` and `validate --assets assets_dev`, then the board. Each Python step runs under an 8 GB
cgroup cap (systemd-run --user --scope -p MemoryMax=8G), one at a time; Chrome runs inside the capped steps. The
log goes to planes/run_<pair>.log. Codex paints separately (planes_concepts.py), once per image.

    planes_run.py p12            (later p34)
"""
import subprocess
import sys
from pathlib import Path

import planes_design as D

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OYMAP = ROOT / 'openyamm-studio/build-xeen/oymap'
CAP = ['systemd-run', '--user', '--scope', '-q', '-p', 'MemoryMax=8G']


def step(log, command, cwd=HERE):
    log.write(f'$ {" ".join(str(c) for c in command)}\n')
    log.flush()
    result = subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        log.write(f'FAILED ({result.returncode})\n')
        sys.exit(f'failed: {command}')


def main():
    pair = sys.argv[1] if len(sys.argv) > 1 else 'p12'
    keys = D.PAIRS[pair]
    with open(HERE / 'planes' / f'run_{pair}.log', 'w') as log:
        step(log, CAP + ['python3', 'planes_render.py', *keys, '--png'])
        step(log, CAP + ['python3', 'planes_brief.py', *keys])
        for key in keys:
            brief = ROOT / 'devdocs/xeen/briefs' / key / 'L1'
            step(log, [OYMAP, 'fmt', brief], ROOT)
            step(log, [OYMAP, 'fmt', '--check', brief], ROOT)
            step(log, [OYMAP, 'validate', brief, '--assets', ROOT / 'assets_dev'], ROOT)
        step(log, CAP + ['python3', 'board_planes.py', pair])
    print((HERE / 'planes' / f'run_{pair}.log').read_text())


if __name__ == '__main__':
    main()
