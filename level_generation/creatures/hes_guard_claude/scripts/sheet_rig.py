"""Simulated cloth sheets (creature.json "sheets": a cape hanging from the shoulders), generalised from the Moon
Cleric's banner_rig.py: NCOL columns per sheet spread by ANGLE round the body axis (a cape wraps the back and sides),
each a chain of NSEG bones from the sheet's top edge in that column straight down to its lowest point, parented to
the sheet's root bone (B_Spine2); every vertex blends its two neighbouring columns (by angle) and two height bones.
The chain's 'deg' is its column angle, so robe_sim.py's one-sided collisions push it outward from the body. Simulated
by robe_sim.py (CHAINS_KEY=sheet_chains ROOT=B_Spine2 PREFIX=Sheet_), neighbours kept inside each sheet only.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; scene = bpy.context.scene
co = np.array([v.co[:] for v in me.vertices])
pv = np.array([a.value for a in me.attributes['piece'].data])
pel = np.array(rig.data.bones['B_Pelvis'].head_local)
chains, plan = [], []
for sh in cfg.C['sheets']:
    ids = np.where(pv == sh['piece'])[0]; c = co[ids]
    ang = np.degrees(np.arctan2(c[:, 0] - pel[0], c[:, 1] - pel[1]))           # 0 = straight behind (+Y)
    ncol, nseg = sh['ncol'], sh['nseg']
    lo, hi = np.percentile(ang, 2), np.percentile(ang, 98)
    cols = []
    for k, a in enumerate(np.linspace(lo, hi, ncol)):
        band = c[np.abs(((ang - a + 180) % 360) - 180) < max(6.0, (hi - lo) / ncol / 2)]
        top = band[np.argmax(band[:, 2])]; bot = band[np.argmin(band[:, 2])]
        r_top = float(np.hypot(top[0] - pel[0], top[1] - pel[1])); r_bot = float(np.hypot(bot[0] - pel[0], bot[1] - pel[1]))
        ar = math.radians(a)
        P = lambda r, z: np.array([pel[0] + math.sin(ar) * r, pel[1] + math.cos(ar) * r, z])
        pts = [P(r_top + (r_bot - r_top) * j / nseg, top[2] + (bot[2] - top[2]) * j / nseg) for j in range(nseg + 1)]
        names = [f"Sheet_{sh['name']}{k}_{j}" for j in range(nseg)]
        chains.append({'deg': float(a), 'group': sh['name'], 'pts': [p.tolist() for p in pts], 'bones': names, 'root': sh['root']})
        cols.append((a, top[2], bot[2], names))
    plan.append((ids, ang, cols, nseg))
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
for ch in chains:
    parent = rig.data.edit_bones[ch['root']]
    for k, n in enumerate(ch['bones']):
        b = rig.data.edit_bones.get(n) or rig.data.edit_bones.new(n)
        b.head = ch['pts'][k]; b.tail = ch['pts'][k + 1]; b.parent = parent; b.use_connect = k > 0; parent = b
bpy.ops.object.mode_set(mode='OBJECT')
groups = {g.name: g for g in body.vertex_groups}
for ch in chains:
    for n in ch['bones']:
        if n not in groups:
            groups[n] = body.vertex_groups.new(name=n)
for ids, ang, cols, nseg in plan:
    ca = np.array([c[0] for c in cols])
    for i, a in zip(ids, ang):
        z = co[i, 2]
        for g in body.vertex_groups:
            g.remove([int(i)])
        t_ = float(np.interp(a, ca, np.arange(len(ca)))); lo = int(math.floor(t_)); hi = min(lo + 1, len(ca) - 1); t = t_ - lo
        w = {}
        for ci, mix in ((lo, 1 - t), (hi, t)):
            _, ztop, zbot, names = cols[ci]
            u = float(np.clip((ztop - z) / max(ztop - zbot, 1e-6), 0, 1)) * nseg
            k = min(nseg - 1, int(u)); v = u - k
            w[names[k]] = w.get(names[k], 0) + mix * (1 - v * (k + 1 < nseg))
            if k + 1 < nseg:
                w[names[k + 1]] = w.get(names[k + 1], 0) + mix * v
        best = sorted(w.items(), key=lambda kv: -kv[1])[:4]; s = sum(v for _, v in best)
        for n, v in best:
            if v > 1e-6:
                groups[n].add([int(i)], v / s, 'REPLACE')
scene['sheet_chains'] = json.dumps(chains)
print('SHEETS chains', len(chains), 'bones', len(rig.data.bones), 'angles', [round(c['deg'], 1) for c in chains])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
