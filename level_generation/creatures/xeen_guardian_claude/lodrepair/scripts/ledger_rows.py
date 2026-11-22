#!/usr/bin/env python3
"""Markdown rows for REDUCTION_LEDGER.md from a repair run's install log: far-LOD triangles before and after.
Usage: ledger_rows.py <run name> <date>"""
import json
import struct
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
run, date = sys.argv[1], sys.argv[2]


def lod_triangles(path):
    """Triangles of LOD0 and each colour LOD of the GLB's largest LOD mesh."""
    raw = path.read_bytes()
    document = json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])
    count = lambda mesh: sum(document['accessors'][p['indices']]['count'] // 3 for p in mesh['primitives'])
    chains = [[count(m)] + [count(document['meshes'][i]) for i in m['extras']['openyamm_lods']]
              for m in document['meshes'] if (m.get('extras') or {}).get('openyamm_lods')]
    return max(chains)


names = {}
for manifest in (PROJECT.parents[2] / 'assets_dev').glob('worlds/*/models/actors.yml'):
    descriptor = None
    for text in manifest.read_text().splitlines():
        if text.startswith('- descriptor: '):
            descriptor = text[len('- descriptor: '):].strip()
        elif text.startswith('  model: ') and descriptor:
            names.setdefault(Path(text.split()[-1]).stem, descriptor.rsplit(' ', 1)[0])
print('| Model | File | LOD2 before -> after | LOD3 before -> after | Budget (LOD2/LOD3 of LOD0) | Status | Rollback source |')
print('|---|---|---|---|---|---|---|')
for line in (PROJECT / 'work' / run / 'install.log').read_text().splitlines():
    if not line.startswith('INSTALLED'):
        continue
    _, stem, world, step = line.split()
    before = lod_triangles(PROJECT / 'originals' / f'{stem}.glb')
    after = lod_triangles(PROJECT / 'export' / f'{stem}.glb')
    lod2 = f'{before[2]:,} -> {after[2]:,}' if len(before) > 2 else '-'
    lod3 = f'{before[3]:,} -> {after[3]:,}' if len(before) > 3 else '-'
    budget = '/'.join(f'{int(x)} %' for x in step[1:].split('_'))
    print(f'| {names.get(stem, stem)} | `{stem}.glb` | {lod2} | {lod3} | {budget} | installed {date} | '
          f'`lod_repair_claude/originals/{stem}.glb` |')
