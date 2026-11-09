"""Sleeve cuffs stay on the forearm (mm9_tryggva, sleeve-poke gate 2026-11-02): fit_rig.py's nearest-MM9-bone labels gave some
sleeve vertices up to 8 cm above the wrist Hand weight; in MM9's limp death hand (wrist 127 deg) they swung in with the
hand and the grafted stub (Forearm) came 15 mm through the cloth. Body-material (not hand, not head) vertices of each arm
move their Hand weight onto the Forearm by a ramp along the forearm axis: all of it below KEEP0 x the forearm length,
none past KEEP1 (the cuff's last centimetres still bend a little with the wrist). Weights only (UVs, paint unchanged).
Args (Blender): -- <in blend> <out blend> [keep0 0.92] [keep1 1.04]"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
K0 = float(a[2]) if len(a) > 2 else 0.92
K1 = float(a[3]) if len(a) > 3 else 1.04
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
hand = np.zeros(len(me.polygons), np.int32); head = np.zeros(len(me.polygons), np.int32)
me.attributes['hand'].data.foreach_get('value', hand); me.attributes['head'].data.foreach_get('value', head)
bodyv = np.zeros(len(me.vertices), bool)
handv = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    for v in p.vertices:
        if hand[p.index] or head[p.index]:
            handv[v] = True
        else:
            bodyv[v] = True
bodyv &= ~handv                     # vertices shared with the graft keep their weights
mw = body.matrix_world
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
rep = {}
for s in 'LR':
    hg, fg = body.vertex_groups[f'Bip01 {s} Hand'], body.vertex_groups[f'Bip01 {s} Forearm']
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s} Hand'].head_local)
    L = np.linalg.norm(a1 - a0); ax = (a1 - a0) / L
    n, moved = 0, 0.0
    for v in me.vertices:
        if not bodyv[v.index]:
            continue
        g = next((g for g in v.groups if g.group == hg.index), None)
        if g is None or g.weight <= 0:
            continue
        t = float((CO[v.index] - a0) @ ax) / L
        if np.linalg.norm(np.cross(CO[v.index] - a0, ax)) > 0.15:
            continue
        k = np.clip((t - K0) / (K1 - K0), 0, 1); k = k * k * (3 - 2 * k)
        take = g.weight * (1 - k)
        if take <= 1e-4:
            continue
        hg.add([v.index], g.weight - take, 'REPLACE')
        fg.add([v.index], take, 'ADD')
        n += 1; moved += take
    rep[s] = {'verts': n, 'weight_moved': round(float(moved), 2)}
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('CUFF_WEIGHTS', json.dumps(rep))
