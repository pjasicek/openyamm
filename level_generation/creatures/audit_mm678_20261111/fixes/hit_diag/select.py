#!/usr/bin/env python3
"""Hit fold group (anim fixes, 2026-11-11): for each model, scale every joint of Hit toward the clip's own first frame
(rotations and translations) by 1.0, 0.7, 0.6, 0.5, 0.4 and report the spine/head/arm/hand bad share beyond the idle
clip (Standing, else Flight or Walking). Usage: select.py <stem> ... > select.txt"""
import subprocess, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared'))
import motion_audit  # noqa
ROOT = Path(__file__).resolve().parents[5]
for s in sys.argv[1:]:
    w = s.split('_')[0]
    G = ROOT / f'assets_source/worlds/{w}/models/{s}.glb'
    base = motion_audit.Audit(G)
    idle = next(c for c in ('Standing', 'Flight', 'Walking', 'Fly') if c in base.model.clips)
    ref = {k: v['bad_pct'] for k, v in base.clip(idle, 30)[0]['deform'].items()}
    row = []
    for f in [float(x) for x in __import__("os").environ.get("FACTORS", "1.0,0.7,0.6,0.5,0.4").split(",")]:
        subprocess.run([sys.executable, '../anim_tools/scale_keys.py', str(G), 'work.glb', '--clip', 'Hit', '--joints', '*',
                        '--factor', str(f), '--ref', 'Hit', '--translation-joints', '*', '--translation-factor', str(f)],
                       check=True, capture_output=True)
        a = motion_audit.Audit('work.glb')
        d = {k: v['bad_pct'] for k, v in a.clip('Hit', 30)[0]['deform'].items()}
        beyond = {k: round(d[k] - ref.get(k, 0), 1) for k in ('spine', 'head', 'arm', 'hand', 'cloth') if k in d}
        row.append((f, max(beyond.values()), beyond))
    ok = [r for r in row if r[1] < 12]
    pick = ok[0][0] if ok else None
    print(json.dumps({'stem': s, 'idle': idle, 'pick': pick, 'rows': row}), flush=True)
