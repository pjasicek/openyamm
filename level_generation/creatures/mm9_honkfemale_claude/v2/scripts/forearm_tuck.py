"""Keep the forearm skin inside the sleeve (Honk female, user 2026-10-31: "right one is protruding from the sleeve").
A flap of skin stood 6-7 cm off the forearm axis at t 0.55-0.8 (the bone is 25 cm, the arm under 3 cm thick). It was hidden
until hand_fix.py centred the sleeve, which moved the wall past it. The flap is the hand-flagged stump of the graft, so hand_fix.py scaled it too. Any skin or stump vertex on the forearm further
from the axis than the limit goes back onto the limit, along its own direction from the axis. The hand starts at t 1, past t1,
so it does not move; weights and UVs do not change.
Args (Blender): <in blend> <out blend> <report json> [t0=0.35 t1=0.92 limit=0.03 limit_end=0.032]
Run last, on braid_v3."""
import bpy, bmesh, sys, json
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = a[:3]
opt = dict(x.split('=', 1) for x in a[3:])
T0, T1 = float(opt.get('t0', 0.35)), float(opt.get('t1', 0.92))
LIM, LIM_END = float(opt.get('limit', 0.03)), float(opt.get('limit_end', 0.032))
bpy.ops.wm.open_mainfile(filepath=IN)
b = bpy.data.objects['Body']; rig = b.parent
M = b.matrix_world; Mi = M.inverted()
bm = bmesh.new(); bm.from_mesh(b.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
heads = {i for i, m in enumerate(b.data.materials) if m and 'head' in m.name.lower()}
skin = {v for f in bm.faces if (f[lh] or f.material_index in heads) and not f[lk] for v in f.verts}
hand = {v for f in bm.faces if f[lk] for v in f.verts}
rep = {'materials': [m.name for m in b.data.materials if m], 'skin_verts': len(skin)}
for s in 'LR':
    e = rig.matrix_world @ rig.data.bones[f'Bip01 {s} Forearm'].head_local
    w = rig.matrix_world @ rig.data.bones[f'Bip01 {s} Hand'].head_local
    L = (w - e).length; ax = (w - e).normalized()
    moved = 0; worst = 0.0
    for v in skin | hand:
        p = M @ v.co; d = p - e; along = d.dot(ax); t = along / L
        if t < T0 or t > T1:
            continue
        r = d - ax * along; rad = r.length
        if rad > 0.13 or rad < 1e-6:
            continue
        k = max(0.0, min(1.0, (t - 0.8) / 0.12)); lim = LIM + (LIM_END - LIM) * k
        if rad > lim:
            v.co = Mi @ (e + ax * along + r * (lim / rad))
            moved += 1; worst = max(worst, rad)
    rep[s] = {'moved': moved, 'worst_before_m': round(worst, 4)}
bm.to_mesh(b.data); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('TUCK', rep)
