"""Slim the hidden legs and hips under the dress (in place on work/rig_textured_uv.blend; recomputed from the stored
originals in 'leg_rest_co'; the applied setting is the mesh property 'm428_legs_slimmed').

Review 2026-10-19: in Running (and a little in Walking) the hips and the backs of the thighs of the hidden leg piece
pushed through the back of the dress between the cloth chains (dark hose patches, review/hips/frames). The legs are
seen only as shoes under the hem, so the leg piece (piece 1) is pulled toward its bones at rest: above the calf the
offset from the nearest leg-bone segment (thigh, calf) shrinks by up to SHRINK (ramp Z0 -> Z1; first tried
0.30 -> 0.55 m, which left calf patches in Running); the hip/buttock
region above the crotch shrinks toward the pelvis axis by the same factor. Shoes and ankles are untouched. UVs,
weights and topology are unchanged."""
import bpy
import numpy as np
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
SHRINK = 0.40
Z0, Z1 = 0.17, 0.40                                  # ramp heights (m); ankles (0.145) and shoes untouched
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/rig_textured_uv.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
# originals are kept in the point attribute 'leg_rest_co' so the slimming can be re-tuned from the authored shape
if 'leg_rest_co' not in me.attributes:
    src = P / 'work/rig_textured_uv_pre_handfix.blend'     # one-off: the first run (0.30-0.55 ramp) did not store them
    with bpy.data.libraries.load(str(src), link=False) as (_, dst):
        dst.meshes = ['Body']
    orig = dst.meshes[0]; assert len(orig.vertices) == len(me.vertices)
    a = me.attributes.new('leg_rest_co', 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set('vector', [c for v in orig.vertices for c in v.co])
    bpy.data.meshes.remove(orig)
REST = np.zeros(len(me.vertices) * 3); me.attributes['leg_rest_co'].data.foreach_get('vector', REST); REST = REST.reshape(-1, 3)
already = me.get('m428_legs_slimmed') == f'{SHRINK}:{Z0}:{Z1}'
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
B = lambda n: np.array(rig.data.bones[n].head_local)
segs = [(B(f'B_{s}_Thigh'), B(f'B_{s}_Calf')) for s in 'LR'] + [(B(f'B_{s}_Calf'), B(f'B_{s}_Foot')) for s in 'LR']
pel = B('B_Pelvis'); crotch = min(B('B_L_Thigh')[2], B('B_R_Thigh')[2]) - 0.035
moved = 0; maxd = 0.0
for v in ([] if already else me.vertices):
    if pv[v.index] != 1:
        continue
    p = REST[v.index].copy(); z = p[2]
    s = SHRINK * float(np.clip((z - Z0) / (Z1 - Z0), 0, 1))
    if s <= 0:
        v.co = Vector(p); continue
    if z > crotch:                                    # hips and buttocks: toward the pelvis axis (vertical line)
        q = np.array([pel[0], pel[1], z])
    else:
        best = None
        for a, b in segs:
            ab = b - a; t = np.clip((p - a) @ ab / (ab @ ab), 0, 1); c = a + t * ab
            if best is None or np.linalg.norm(p - c) < np.linalg.norm(p - best):
                best = c
        q = best
    new = p + (q - p) * s
    maxd = max(maxd, float(np.linalg.norm(new - p))); v.co = Vector(new); moved += 1
if not already:
    me.update(); me['m428_legs_slimmed'] = f'{SHRINK}:{Z0}:{Z1}'
    bpy.ops.wm.save_mainfile()
print('LEGS already slimmed' if already else 'LEGS slimmed', moved, 'leg-piece vertices by up to', SHRINK, '; max move cm', round(maxd * 100, 2))
