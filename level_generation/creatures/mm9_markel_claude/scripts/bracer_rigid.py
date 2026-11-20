"""Rigid steel bracers (mm9_sven, 2026-11-02): sleeve_poke_gate.py flagged 13-25 mm in bent-wrist frames although the stub
under the bracer follows the forearm; the bracer's own rim vertices carried hand weight, so the metal bent inward with the
wrist and the stub showed through. Every body (non-hand) vertex of each arm from SPAN_UP above the hand joint to the
bracer rim, within RADIUS of the forearm axis, takes 100 % Bip01 <side> Forearm (the playbook rule: a rigid bracer takes
the wrist rigidly). Weights only; geometry, UVs and attributes unchanged. Args (Blender): -- <in blend> <out blend>
[span_up 0.14]"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
SPAN_UP = float(a[2]) if len(a) > 2 else 0.14
RADIUS = 0.10
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
hand_attr = np.zeros(len(me.polygons), np.int32)
me.attributes['hand'].data.foreach_get('value', hand_attr)
handv = set(i for p in me.polygons if hand_attr[p.index] for i in p.vertices)
headv = set()
if 'head' in me.attributes:
    head_attr = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', head_attr)
    headv = set(i for p in me.polygons if head_attr[p.index] for i in p.vertices)
gname = {g.index: g.name for g in body.vertex_groups}
BONES = {b.name for b in rig.data.bones}
rep = {}
for tok in ('L', 'R'):
    arm = {f'Bip01 {tok} {k}' for k in ('UpperArm', 'Forearm', 'Hand')}
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    L = np.linalg.norm(a1 - a0); axis = (a1 - a0) / L
    fa = body.vertex_groups[f'Bip01 {tok} Forearm']
    n = 0
    for v in me.vertices:
        i = v.index
        if i in handv or i in headv:
            continue
        w = {gname[g.group]: g.weight for g in v.groups if g.weight > 0 and gname[g.group] in BONES}
        if not w or max(w, key=w.get) not in arm:
            continue
        t = (CO[i] - a0) @ axis
        if t < L - SPAN_UP or t > L + 0.05 or np.linalg.norm(np.cross(CO[i] - a0, axis)) > RADIUS:
            continue
        for g in list(v.groups):
            if gname[g.group] in BONES:
                body.vertex_groups[g.group].remove([i])
        fa.add([i], 1.0, 'REPLACE')
        n += 1
    rep[tok] = n
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('BRACER_RIGID', rep)
