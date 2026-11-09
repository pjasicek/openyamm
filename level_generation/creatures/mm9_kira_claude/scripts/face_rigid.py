"""The face moves rigidly with the Head (user review 2026-11-02, Fidget frame 55: "left cheek/chin distorted").

Cause: rig_kira.py split the face-and-neck skin (part 20) between Head and Neck by a chin-nape plane through the CHIN
(front point z 0.69 = the chin's front, blend +/-3 cm), and helpers_kira.py relaxed the neck band 10 passes up to z 0.72:
the lips, chin and jaw (z 0.67-0.72) carried 30-100 % Neck / Bip01 Head_h. KIRA.abc has no jaw bone; MM9's Head
pivot sits at the mouth (z 0.70), so every head turn against the neck (Fidget 1.8 s, the Sc2 talk clips) sheared
the lower face: up to 7.7 cm off the head-rigid position (the chin in Death, Sc2_KIRA20_23 8.3 cm on the throat).

Fix (weights only; UVs, geometry and the paint unchanged): a boundary that follows the jaw instead of a plane through
the chin. z_b(x, y) = Z0 + SLOPE * (y - Y0) + CURVE * x^2: under the chin at the throat corner (y -0.02, z 0.664),
rising to the nape (y 0.07, z 0.715) and towards the jaw angles (x 0.05: +3 mm). Head fraction
t = smoothstep(z - z_b, -LO, HI) over 1.8 cm, shared between Neck / Bip01 Head_h / Head as helpers_kira.py does
(Head = 2t-1, Head_h = 1-|2t-1|, Neck = 1-2t, of the vertex's Head+Head_h+Neck total; Neck_h and Spine3 kept).
Behind the jaw angle (y > YB) the line rises BACK x (y - YB) more, capped at ZMAX, and the blend doubles: the skin under
the ears and over the nape keeps a soft neck share (with the whole jaw rigid, a hard line there opened the skin's
jagged edge under the hanging hair in Sc2_Kira7/17/20-23). Everything in front of the jaw angle above the jaw line
(chin, jaw underside, lips, cheeks) is Head 1.0. Args: <in blend> <out blend>"""
import bpy, sys, json
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
Z0, Y0, SLOPE, CURVE, LO, HI = 0.664, -0.02, 0.57, 1.2, 0.010, 0.008
YB, BACK, ZMAX, WIDE = -0.005, 0.6, 0.73, 1.0
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
n = len(me.vertices)
face = np.zeros(n, bool)
for p in me.polygons:
    if fp[p.index] == 20:
        face[list(p.vertices)] = True
gi = {g.name: g.index for g in body.vertex_groups}
H, HH, NK = 'Bip01 Head', 'Bip01 Head_h', 'Bip01 Neck'
for k in (H, HH, NK):
    if k not in gi: gi[k] = body.vertex_groups.new(name=k).index
P = np.array([v.co[:] for v in me.vertices])
def sst(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
back = np.clip(P[:, 1] - YB, 0, None)                  # behind the jaw angle (under the ears, the nape)
zb = np.minimum(Z0 + SLOPE * (P[:, 1] - Y0) + CURVE * P[:, 0] ** 2 + BACK * back, ZMAX)
wide = 1 + WIDE * sst(P[:, 1], YB, YB + 0.03)
T = sst(P[:, 2] - zb, -LO * wide, HI * wide)
changed, head_before, head_after = 0, [], []
for i in np.nonzero(face)[0].tolist():
    v = me.vertices[i]
    w = {body.vertex_groups[g.group].name: g.weight for g in v.groups if g.weight > 0}
    tot = w.get(H, 0) + w.get(HH, 0) + w.get(NK, 0)
    if tot <= 1e-6:
        continue
    t = float(T[i])
    new = {H: tot * max(2 * t - 1, 0), HH: tot * (1 - abs(2 * t - 1)), NK: tot * max(1 - 2 * t, 0)}
    if all(abs(new[k] - w.get(k, 0)) < 1e-4 for k in new):
        continue
    head_before.append(w.get(H, 0) / sum(w.values())); changed += 1
    for k in (H, HH, NK):
        w[k] = new[k]
    top = sorted(((k, x) for k, x in w.items() if x > 0.01), key=lambda kv: -kv[1])[:4]
    s = sum(x for _, x in top)
    for g in [g.group for g in v.groups]:
        body.vertex_groups[g].remove([i])
    for k, x in top:
        if k not in gi: gi[k] = body.vertex_groups.new(name=k).index
        body.vertex_groups[gi[k]].add([i], x / s, 'REPLACE')
    head_after.append(dict(top).get(H, 0) / s)
# report: the lower face (front, between the throat corner and the nose)
low = face & (P[:, 1] < -0.03) & (P[:, 2] > 0.672) & (P[:, 2] < 0.74)
hw = np.array([sum(g.weight for g in me.vertices[i].groups if body.vertex_groups[g.group].name == H) for i in np.nonzero(low)[0]])
rep = dict(changed=changed, lower_face_verts=int(low.sum()), lower_face_head_min=round(float(hw.min()), 3),
           head_mean_before=round(float(np.mean(head_before)), 3), head_mean_after=round(float(np.mean(head_after)), 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FACERIGID ' + json.dumps(rep))
