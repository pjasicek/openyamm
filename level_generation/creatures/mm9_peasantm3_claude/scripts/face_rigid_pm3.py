"""The face moves rigidly with the Head (VARIANTS_BRIEF, user review 2026-11-02; Kira's face_rigid.py adapted).

Probe (face_weights_probe.py on work/texpass_head.blend): the head-set skin at z 0.69-0.72 (chin, jaw, lower lip) carried
35-65 % Bip01 Neck (fit_rig.py's MM9 labels diffused across the chin), so every head turn against the neck would shear
the lower face. The PeasantMale skeleton has no jaw or Head_h bone.

Fix (weights only; UVs, geometry and paint unchanged): a boundary that follows the jaw instead of a level line.
z_b(x, y) = Z0 + SLOPE * (y - Y0) + CURVE * x^2 (+ BACK * (y - YB) behind the jaw angle, capped at ZMAX): under the chin
at the throat corner (jaw_profile.py: mid-plane throat y -0.032 z 0.65-0.68, chin underside z 0.69-0.70; jaw angle x 0.05
at z 0.70-0.71, y -0.01), rising to the nape. Head fraction t = smoothstep(z - z_b, -LO, HI). Each head-set vertex's
Head share of its Head+Neck total becomes max(t, its current share): the face only becomes more rigid, the nape keeps
what MM9's labels gave it where that is more. Args (Blender): <in blend> <out blend>"""
import bpy, sys, json
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
Z0, Y0, SLOPE, CURVE, LO, HI = 0.676, -0.035, 0.45, 1.2, 0.010, 0.008
YB, BACK, ZMAX = 0.0, 0.4, 0.725
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
hf = np.zeros(len(me.polygons), int); me.attributes['head'].data.foreach_get('value', hf)
face = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if hf[p.index]:
        face[list(p.vertices)] = True
gi = {g.name: g.index for g in body.vertex_groups}
H, NK = 'Bip01 Head', 'Bip01 Neck'
P = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])


def sst(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


back = np.clip(P[:, 1] - YB, 0, None)
zb = np.minimum(Z0 + SLOPE * (P[:, 1] - Y0) + CURVE * P[:, 0] ** 2 + BACK * back, ZMAX)
T = sst(P[:, 2] - zb, -LO, HI)
changed = 0
for i in np.nonzero(face)[0].tolist():
    v = me.vertices[i]
    w = {body.vertex_groups[g.group].name: g.weight for g in v.groups if g.weight > 0}
    tot = w.get(H, 0) + w.get(NK, 0)
    if tot <= 1e-6:
        continue
    cur = w.get(H, 0) / tot
    t = max(float(T[i]), cur)
    if t - cur < 1e-4:
        continue
    changed += 1
    w[H], w[NK] = tot * t, tot * (1 - t)
    top = sorted(((k, x) for k, x in w.items() if x > 0.01), key=lambda kv: -kv[1])[:4]
    s = sum(x for _, x in top)
    for g in [g.group for g in v.groups]:
        body.vertex_groups[g].remove([i])
    for k, x in top:
        if k not in gi:
            gi[k] = body.vertex_groups.new(name=k).index
        body.vertex_groups[gi[k]].add([i], x / s, 'REPLACE')
# report: the lower face (front of the throat corner, from the chin underside to the nose)
low = face & (P[:, 1] < -0.04) & (P[:, 2] > 0.69) & (P[:, 2] < 0.76)
hw = np.array([sum(g.weight for g in me.vertices[i].groups if body.vertex_groups[g.group].name == H)
               for i in np.nonzero(low)[0]])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FACERIGID ' + json.dumps(dict(changed=changed, lower_face_verts=int(low.sum()),
                                     lower_face_head_min=round(float(hw.min()), 3),
                                     lower_face_head_mean=round(float(hw.mean()), 3))))
