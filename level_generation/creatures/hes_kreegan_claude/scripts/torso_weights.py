"""hkr G4: the demon's chest and back skin hang on the clavicles (and a little on the upper arms) right to the
sternum and the spine, so every shrug of the set's clips slid the torso skin 2-5 cm under the rigid chest and back
plates. Inner torso vertices (|x| < X1, Z0 < z < Z1, dominant bone a clavicle, upper arm or B_Spine*) hand their
clavicle and upper-arm share to B_Spine2 by w(|x|) = 1 inside X0, smoothstep to 0 at X1 (the shoulders keep theirs);
the shoulder-spike clusters (dominant Bone_041 / Bone_036, weight > 0.5) become rigid on that bone, which
pauldron_bones.py re-parents to the pauldron bone (the pauldron covers their roots). Args: -- <in> <out>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
X0, X1, Z0, Z1 = (float(os.environ.get(k, d)) for k, d in (('X0', '0.12'), ('X1', '0.24'), ('Z0', '1.12'), ('Z1', '1.50')))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
body = bpy.data.objects['Body']; me = body.data
G = {g.name: g for g in body.vertex_groups}; GI = {g.index: g.name for g in body.vertex_groups}
moved = rigid = 0
for v in me.vertices:
    co = body.matrix_world @ v.co
    ws = {GI[g.group]: g.weight for g in v.groups}
    if not ws: continue
    dom = max(ws, key=ws.get)
    for sp in ('Bone_041', 'Bone_036'):
        if ws.get(sp, 0) > 0.5:
            for n in ws: G[n].remove([v.index])
            G[sp].add([v.index], 1.0, 'REPLACE'); rigid += 1; ws = None; break
    if ws is None: continue
    ax = abs(co.x)
    if not (Z0 < co.z < Z1 and ax < X1): continue
    if not any(t in dom for t in ('Clavicle', 'UpperArm', 'Spine', 'Bone_024')): continue   # Bone_024: the harness straps
    t = min(1.0, max(0.0, (X1 - ax) / (X1 - X0))); w = t * t * (3 - 2 * t)
    give = 0.0
    for n in list(ws):
        if 'Clavicle' in n or 'UpperArm' in n:
            d = ws[n] * w; give += d; ws[n] -= d
            if ws[n] > 1e-4: G[n].add([v.index], ws[n], 'REPLACE')
            else: G[n].remove([v.index])
    if give > 0:
        G['B_Spine2'].add([v.index], ws.get('B_Spine2', 0.0) + give, 'REPLACE'); moved += 1
print('TORSOW moved', moved, 'vertices to B_Spine2; rigid spike vertices', rigid)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[1]))
