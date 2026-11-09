"""Last vertex and weight fixes before the runtime build (Honk bodies).
- Small loose body parts (belt buckle bits, medallion, trim shards): rigid on one weight set, the weights of the main-body
  vertex nearest the part's centre, so they stay on the belt or chest (Fidget lifted the buckle 6.5 mm off the belt).
- Lips: Meshy's two lip plates meet at a jagged line. Their rim vertices (within `lip_rim` of `lip_z` in height, optional)
  snap to one smooth curve z(x) (quadratic fit), upper and lower `lip_gap` apart.
Args (Blender): <in blend> <out blend> <report json> [lip_z=.. lip_rim=.. lip_gap=.. lip_x=x0,x1 small=120 keep=<part list>]"""
import bpy, bmesh, json, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
opt = dict(x.split('=', 1) for x in a[3:])
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data; M = b.matrix_world; Mi = M.inverted()
rig = b.parent
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
CO = np.array([tuple(M @ v.co) for v in me.vertices])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh = bm.faces.layers.int['head']; lk = bm.faces.layers.int['hand']
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
vhead = np.zeros(len(bm.verts), bool); vhand = np.zeros(len(bm.verts), bool)
for f in bm.faces:
    for v in f.verts:
        vhead[v.index] |= f[lh] == 1; vhand[v.index] |= f[lk] == 1
bm.free()
SMALL = int(opt.get('small', 120))
sizes = np.bincount(comp)
small = [k for k in range(cid) if sizes[k] < SMALL and not vhead[comp == k].any() and not vhand[comp == k].any()]
main = np.where(~np.isin(comp, small) & ~vhead & ~vhand)[0]
rep = {'parts': cid, 'small': {}}
for k in small:
    m = np.where(comp == k)[0]
    c = CO[m].mean(0)
    near = main[np.argsort(np.linalg.norm(CO[main] - c, axis=1))[:10]]     # mean of the 10 nearest: a buckle spans the belt's own blend
    acc = {}
    for i in near:
        for g in me.vertices[int(i)].groups:
            acc[g.group] = acc.get(g.group, 0) + g.weight / len(near)
    top = sorted(acc.items(), key=lambda x: -x[1])[:4]
    tot = sum(x for _, x in top)
    w = [(g, x / tot) for g, x in top]
    for g in b.vertex_groups:
        g.remove(m.tolist())
    for gi, wt in w:
        b.vertex_groups[gi].add(m.tolist(), wt, 'REPLACE')
    rep['small'][int(k)] = {'verts': len(m), 'centre': c.round(3).tolist(), 'from': [b.vertex_groups[gi].name for gi, _ in w]}
if 'lip_z' in opt:
    z0, rim, gap = float(opt['lip_z']), float(opt['lip_rim']), float(opt.get('lip_gap', 0.0006))
    x0, x1 = [float(x) for x in opt.get('lip_x', '-0.04,0.03').split(',')]
    big = np.argmax(sizes)
    head_parts = [k for k in range(cid) if vhead[comp == k].any() and sizes[k] < 200]
    lips = [k for k in head_parts if abs(np.median(CO[comp == k, 2]) - z0) < 0.03 and CO[comp == k, 1].max() < -0.04]
    rep['lip_parts'] = [int(k) for k in lips]
    up, lo = [], []
    for k in lips:
        m = np.where((comp == k) & (np.abs(CO[:, 2] - z0) < rim) & (CO[:, 0] > x0) & (CO[:, 0] < x1))[0]
        (up if np.median(CO[comp == k, 2]) > z0 else lo).append(m)
    up, lo = np.concatenate(up), np.concatenate(lo)
    allv = np.concatenate([up, lo])
    cx = 0.5 * (CO[allv, 0].min() + CO[allv, 0].max())
    p = np.polyfit(CO[allv, 0] - cx, CO[allv, 2], 2)
    Curve = lambda x: np.polyval(p, x - cx)
    for idx, sgn in ((up, 1), (lo, -1)):
        for i in idx:
            q = CO[i].copy(); q[2] = Curve(q[0]) + sgn * gap / 2
            me.vertices[i].co = Mi @ __import__('mathutils').Vector(q.tolist())
    rep['lip_verts'] = [len(up), len(lo)]
    rep['lip_curve'] = [float(x) for x in p]
if 'shell_cut_z' in opt or 'drop_parts' in opt:
    # head shell faces hidden inside a hat (they poke through its brim), and small inner sleeve shards whose LODs invert
    zc = float(opt.get('shell_cut_z', 9))
    head_big = max((k for k in range(cid) if vhead[comp == k].any()), key=lambda k: sizes[k] if CO[comp == k, 2].min() < 0.6 else 0)
    drop = [int(x) for x in opt.get('drop_parts', '').split(',') if x]
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    gone = [f for f in bm.faces if (comp[f.verts[0].index] == head_big and min(CO[v.index, 2] for v in f.verts) > zc) or comp[f.verts[0].index] in drop]
    rep['deleted_faces'] = len(gone)
    bmesh.ops.delete(bm, geom=gone, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(me); bm.free()
json.dump(rep, open(a[2], 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('HONKFIX', json.dumps(rep)[:1500])
