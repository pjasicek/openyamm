#!/usr/bin/env python3
"""Per-piece decimation groups for the Skeleton Warrior (separate rigid pieces, each its own group, as the skeleton
reduction): work/groups.npy (int per mesh_in face: 0 kept exactly, k >= 1 one group), work/group_plan.json
({group: [base ratio, category, faces]}) and work/sheet_faces.npy (faces that carry a lining; the linings are rebuilt on
export from the reduced outer faces).
Kept exactly (relaxed prio-1 keep set): the skull face = every cranium face visible from outside the head set
(face_flags.py: 1,010 of 1,114; the 104 hidden under the helmet are cut as one group), the mandible, eyes, teeth, the neck
piece under the jaw, the scimitar (its own primitive), the right-hand faces at the grip (fingers within 5 mm of the scimitar
in the fist + one ring) and every piece of KEEP_N faces or fewer (skirt plates of 20-30 faces, small helmet guards, teeth).
Cut per piece: gauntlets (hand, HAND_MIN in the plan), cuirass, spine column, boots, bracers, femurs, calves (rigid),
pauldrons, cuffs, belt, hip bars, the larger skirt plates (sheet: boundary kept, so hems and rims stay), the helmet shell,
brow insignia, horns and guards (helm)."""
import json, os, re, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
from pieces import pieces  # noqa: E402
KEEP_N = int(os.environ.get('KEEP_N', 30))
V, F, mat, comp, info = pieces(str(HERE / 'work'))
fl = np.load(HERE / 'work' / 'face_flags.npz')
groups = np.zeros(len(F), int); plan = {}; g = 0
head = {k: i for k, i in info.items() if i['mat'] == 1}
order = sorted(head, key=lambda k: -head[k]['n'])
cranium, mandible = order[0], order[1]
mz = head[mandible]['cen'][2]
face_keep = {cranium, mandible}
for k, i in head.items():
    if i['size'] < 0.03 or i['cen'][2] < mz:      # eyes (2.5 cm spheres), teeth; the neck piece under the jaw
        face_keep.add(k)
assert (fl['cranium'] == (comp == cranium)).all()
names = {}
for k, i in sorted(info.items()):
    s = np.where(comp == k)[0]; n = i['n']
    if i['mat'] == 2:
        continue
    if k == cranium:
        hid = s[~fl['visible'][s]]
        g += 1; groups[hid] = g; plan[g] = [0.5, 'hidden', len(hid)]
        continue
    if k in face_keep or n <= KEEP_N:
        continue
    if i['mat'] == 1:
        cat = 'helm'
    elif re.search('Hand|Thumb|Index|Middle|Ring|Pinky', i['bone']):
        cat = 'hand'
    elif i['open']:
        cat = 'sheet'
    else:
        cat = 'rigid'
    sel = s[~fl['grip'][s]] if cat == 'hand' else s
    g += 1; groups[sel] = g; plan[g] = [0.6, cat, len(sel)]; names[g] = f"{i['bone']} n{n}"
np.save(HERE / 'work' / 'groups.npy', groups)
np.save(HERE / 'work' / 'sheet_faces.npy', fl['lined'])
json.dump(plan, open(HERE / 'work' / 'group_plan.json', 'w'))
json.dump(names, open(HERE / 'work' / 'group_names.json', 'w'), indent=0)
lined_groups = sorted({int(x) for x in np.unique(groups[fl['lined']]) if x})
part = [int(fl['lined'][groups == q].mean() * 100) for q in lined_groups]
print('lined groups (percent lined)', dict(zip(lined_groups, part)))
tot = len(F) - int((mat == 2).sum()); kept = int(((groups == 0) & (mat != 2)).sum())
print('GROUPS', g, 'kept faces (body+head)', kept, f'({kept / tot:.1%} of {tot})', 'of which lined', int((fl['lined'] & (groups == 0)).sum()))
cats = {}
for v in plan.values():
    c = cats.setdefault(v[1], [0, 0]); c[0] += 1; c[1] += v[2]
print('per category: groups, faces', cats)
