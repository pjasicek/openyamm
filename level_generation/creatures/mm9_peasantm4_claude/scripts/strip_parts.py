"""PeasantM8 = the ForadDarre mesh (meshcmp: head p90 1.0 cm, torso 0.8, arms 1.4, legs 2.5 = the boot sole 2.6 cm back),
but MM9's PeasantM8a is a balding shopkeeper with short hair to the nape, no necklace. Forad's Meshy body carries a
sculpted ponytail (three loose parts behind the neck), 39 necklace bead parts and two eyeball cups (dropped at export
for Forad). This deletes those loose parts and nothing else (no vertex of the remaining mesh moves: UVs, weights and
the head/hand attributes stay Forad's).
  master <in blend> <out blend> <report json>   (the rigged master 'Body')
  upload <in glb> <out glb> <report json>       (a texturing upload: same classification on its single mesh)
"""
import bpy, bmesh, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
MODE, IN, OUT, REP = argv[:4]


def classify(bm, mw):
    bm.verts.ensure_lookup_table()
    P = np.array([mw @ v.co for v in bm.verts])
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
    # an upload is split at UV seams: join vertices at the same position (connectivity only; nothing is welded)
    key = {}
    for i, q in enumerate(np.round(P * 1e5).astype(np.int64)):
        key.setdefault(tuple(q), []).append(i)
    par = list(range(cid))
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for vs in key.values():
        for j in vs[1:]:
            a, b = find(comp[vs[0]]), find(comp[j])
            if a != b: par[a] = b
    comp = np.array([find(c) for c in comp]); _, comp = np.unique(comp, return_inverse=True); cid = int(comp.max()) + 1
    sizes = np.bincount(comp)
    main = int(sizes.argmax())
    drop = []
    for c in range(cid):
        if c == main: continue
        idx = np.where(comp == c)[0]; Q = P[idx]; ext = np.linalg.norm(Q.max(0) - Q.min(0))
        kind = None
        if 0.76 < Q[:, 2].mean() < 0.81 and Q[:, 1].mean() < -0.05 and len(idx) < 80: kind = 'eye'
        elif len(idx) < 40 and ext < 0.03 and Q[:, 2].max() < 0.70: kind = 'bead'
        elif Q[:, 1].mean() > 0.09 and Q[:, 2].min() > 0.54 and Q[:, 2].max() < 0.76 and len(idx) < 400 \
                and abs(Q[:, 0].mean()) < 0.06: kind = 'ponytail'
        if kind: drop.append((c, int(len(idx)), kind, Q.min(0).round(3).tolist(), Q.max(0).round(3).tolist()))
    return comp, drop


if MODE == 'master':
    bpy.ops.wm.open_mainfile(filepath=IN)
    body = bpy.data.objects['Body']; rig = body.parent
    if rig.animation_data: rig.animation_data.action = None
    for b in rig.pose.bones: b.matrix_basis.identity()
    me = body.data; mw = body.matrix_world
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=IN)
    body = next(o for o in bpy.data.objects if o.type == 'MESH'); me = body.data; mw = body.matrix_world
nf0 = len(me.polygons)
bm = bmesh.new(); bm.from_mesh(me)
comp, drop = classify(bm, mw)
dset = {d[0] for d in drop}
bmesh.ops.delete(bm, geom=[v for v in bm.verts if comp[v.index] in dset], context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
rep = {'faces_before': nf0, 'faces_after': len(me.polygons),
       'dropped': {k: sum(1 for d in drop if d[2] == k) for k in ('eye', 'bead', 'ponytail')},
       'ponytail_parts': [d for d in drop if d[2] == 'ponytail'], 'eye_parts': [d for d in drop if d[2] == 'eye']}
json.dump(rep, open(REP, 'w'), indent=1); print('STRIP', json.dumps(rep))
if MODE == 'master':
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
else:
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=False, export_materials='NONE',
                              export_texcoords=True, export_normals=True, export_apply=False)
