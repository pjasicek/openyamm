"""Vambrace cuffs follow the wrist (sleeve_poke_gate: the glove came out through the vambrace's last 3 cm, which reach past the wrist
joint and were all Forearm, up to 43 mm in Sc2_Kira17). Armour-shell vertices (part 1) of each arm past the hand joint along the
forearm axis blend to the Hand: smoothstep over -1.2..+1.2 cm to 1 (the cuff past the wrist moves with the hand like a glove cuff, a 0.85 cap over -0.5..2 cm left the glove 1.5 cm out in Hit;
the vambrace body stays rigid). Weights only, on the UV blend (UVs and the paid paint unchanged). Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
hand = np.zeros(len(me.polygons), int); me.attributes['hand'].data.foreach_get('value', hand)
vp = np.zeros(len(me.vertices), int)
for p in me.polygons:
    for v in p.vertices:
        if fp[p.index] == 1 and not hand[p.index]: vp[v] = 1
P = np.array([v.co[:] for v in me.vertices])
gi = {g.name: g.index for g in body.vertex_groups}
def sst(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
n = 0
for s in 'LR':
    fa = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s} Forearm'].head_local)
    hd = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s} Hand'].head_local)
    ax = (hd - fa) / np.linalg.norm(hd - fa)
    t = (P - hd) @ ax; r = np.linalg.norm(np.cross(P - hd, ax), axis=1)
    ids = np.nonzero((vp == 1) & (t > -0.005) & (r < 0.08) & (np.sign(P[:, 0]) == np.sign(hd[0])))[0]
    for i in ids.tolist():
        w = float(sst(t[i], -0.012, 0.012))
        if w <= 0: continue
        v = me.vertices[i]
        groups = {body.vertex_groups[g.group].name: g.weight for g in v.groups}
        groups = {k: x * (1 - w) for k, x in groups.items()}
        groups[f'Bip01 {s} Hand'] = groups.get(f'Bip01 {s} Hand', 0) + w
        top = sorted(groups.items(), key=lambda kv: -kv[1])[:4]; tot = sum(x for _, x in top)
        for gidx in [g.group for g in v.groups]: body.vertex_groups[gidx].remove([i])
        for k, x in top:
            if k not in gi: gi[k] = body.vertex_groups.new(name=k).index
            body.vertex_groups[gi[k]].add([i], x / tot, 'REPLACE')
        n += 1
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('CUFF', n)
