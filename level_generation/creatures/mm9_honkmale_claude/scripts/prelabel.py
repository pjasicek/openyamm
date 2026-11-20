"""Face attributes `head` and `hand` before the first UV layout (fresh build: head and old hand faces are packed small
in the body atlas, texpass_uv.py). Args: <in blend> <out blend> <config json>
config: neck_cut_z (parts whose median height is above it are head), include/exclude part numbers (lowest-vertex order,
as head_split.py), hand_along (old hand = faces past this distance along the forearm from the wrist joint, within
hand_radius of the forearm axis), tok L/R joints."""
import bpy, bmesh, json, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(a[2]))
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
me = body.data; mw = body.matrix_world
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(me.vertices), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
bm.free()
parts = {k: dict(n=int((comp == k).sum()), zmed=round(float(np.median(CO[comp == k, 2])), 3), lo=CO[comp == k].min(0).round(3).tolist(), hi=CO[comp == k].max(0).round(3).tolist()) for k in range(cid)}
big = {k for k, p in parts.items() if p['zmed'] > cfg['neck_cut_z']}
big |= set(cfg.get('include', [])); big -= set(cfg.get('exclude', []))
n = len(me.polygons)
head = np.zeros(n, np.int32); hand = np.zeros(n, np.int32)
FV = [list(p.vertices) for p in me.polygons]
for i, vs in enumerate(FV):
    head[i] = comp[vs[0]] in big
bones = rig.data.bones
for s in cfg['sides']:
    W = np.array(rig.matrix_world @ bones[s['hand']].head_local); E = np.array(rig.matrix_world @ bones[s['forearm']].head_local)
    d = (W - E) / np.linalg.norm(W - E)
    rel = CO - W; al = rel @ d; rad = np.linalg.norm(rel - np.outer(al, d), axis=1)
    m = (al > cfg['hand_along']) & (rad < cfg['hand_radius']) & (np.sign(CO[:, 0]) == np.sign(W[0]))
    for i, vs in enumerate(FV):
        if m[vs].all():
            hand[i] = 1
at = me.attributes.get('head') or me.attributes.new('head', 'INT', 'FACE'); at.data.foreach_set('value', head.tolist())
at = me.attributes.get('hand') or me.attributes.new('hand', 'INT', 'FACE'); at.data.foreach_set('value', hand.tolist())
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('PRELABEL', json.dumps({'parts': parts}))
print('PRELABEL head', int(head.sum()), 'hand', int(hand.sum()), 'of', n, 'whole', sorted(big))
