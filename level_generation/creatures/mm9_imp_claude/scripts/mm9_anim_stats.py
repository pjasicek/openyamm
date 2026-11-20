"""Per-clip stats of the MM9 source GLB: which bones move, Yweapon vs hand, finger curl, pelvis height."""
import sys, json
import numpy as np
from pygltflib import GLTF2
sys.path.insert(0, 'level_generation/creatures/mm9_yrsa_claude/v2/scripts')
import clips_mm9 as cm
g, rest, clips = cm.source_clips(sys.argv[1])
names = [n.name for n in g.nodes]
print('rest of nodes', [(n, np.round(rest[n][0], 3).tolist()) for n in ['Scene Root', 'Bip01 Pelvis', 'Xpiv', 'Yweaponbase', 'Yweapon']])
for name, (ch, dur) in clips.items():
    mv = {}
    for (j, p), (t, v) in ch.items():
        if p == 'rotation':
            d = np.degrees(2 * np.arccos(np.clip(np.abs(v @ rest[j][1]), 0, 1)))
            mv[j] = float(d.max())
    fing = {j: round(mv[j], 1) for j in mv if 'R Finger' in j}
    w = {j: round(mv.get(j, 0), 1) for j in ['Yweaponbase', 'Yweapon', 'Xpiv', 'Bip01 R Hand', 'Bip01 L Hand', 'Bip01 Tail', 'Bip01 Tail4']}
    tr = {j: np.round(np.ptp(v, axis=0), 3).tolist() for (j, p), (t, v) in ch.items() if p == 'translation' and np.ptp(v, axis=0).max() > 0.002}
    print(name, round(dur, 3), 'keys', len(next(iter(ch.values()))[0]), 'w', w, 'fingR', list(fing.values())[:12], 'trans', tr)
