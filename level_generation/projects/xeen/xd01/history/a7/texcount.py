#!/usr/bin/env python3
"""Distinct face textures of a built BLV (portals left out), with face counts: texcount.py <map.blv> [more.blv]."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import collections, json, subprocess, sys
R = _REPO_ROOT
for path in sys.argv[1:]:
    out = subprocess.run([sys.executable, R + '/util/map_export.py', 'blv', path], capture_output=True, text=True, check=True).stdout
    faces = json.loads(out)['payload']['faces']
    c = collections.Counter(f['texture_name'] for f in faces if not f['is_portal'] and f['texture_name'])
    print(f'{path}: {len(c)} distinct face textures ({sum(c.values())} faces)')
    for t, n in sorted(c.items()):
        print(f'  {t:12s} {n}')
