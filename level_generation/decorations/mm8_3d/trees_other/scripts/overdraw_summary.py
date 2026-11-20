#!/usr/bin/env python3
"""One line per GLB from overdraw.py: mean over the three views of the layers (no depth test) and of the layers in
front of the opaque depth, and the largest 95th percentile, per LOD. Usage: overdraw_summary.py <id> <glb> [tag]"""
import json, subprocess, sys, os
sid, glb = sys.argv[1], sys.argv[2]; tag = sys.argv[3] if len(sys.argv) > 3 else 'after'
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(os.path.dirname(glb), f'overdraw_{tag}.json')
subprocess.run([sys.executable, os.path.join(here, 'overdraw.py'), glb, '--json', out, '--heat',
                os.path.join(here, '..', 'review', 'overdraw', f'{tag}_{sid}')], check=True, stdout=subprocess.DEVNULL)
r = json.load(open(out)); parts = []
for lod in (0, 1, 2):
    v = [r[f'LOD{lod}_{w}'] for w in ('front', 'three_quarter', 'side')]
    parts.append(f"LOD{lod} all {sum(x['layers_mean'] for x in v) / 3:.2f} (p95 {max(x['layers_p95'] for x in v):.0f})"
                 f" front {sum(x['front_mean'] for x in v) / 3:.2f} (p95 {max(x['front_p95'] for x in v):.0f})")
print('OVERDRAW', sid, ' | '.join(parts))
