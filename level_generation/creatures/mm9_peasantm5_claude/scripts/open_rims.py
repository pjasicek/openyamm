"""List every open boundary loop of 'Body' (rest pose): edges, centre, mean radius, face kind (body / head / hand), the
dominant bone of its vertices, the region mask label of its faces (R tunic, G trousers, B boots, A belt), its height range.
Args (Blender): <blend> [out json] [region mask png]"""
import bpy, bmesh, sys, json
import numpy as np
from collections import Counter
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
mw = body.matrix_world
names = [g.name for g in body.vertex_groups]
bm = bmesh.new(); bm.from_mesh(body.data); bm.edges.ensure_lookup_table()
dl = bm.verts.layers.deform.active
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
seen = set(); loops = []
for e in bm.edges:
    if not e.is_boundary or e.index in seen:
        continue
    lp = []; st = [e]; seen.add(e.index)
    while st:
        x = st.pop(); lp.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y.index not in seen:
                    seen.add(y.index); st.append(y)
    loops.append(lp)
MK = None
if len(a) > 2:
    img = bpy.data.images.load(a[2]); W, H = img.size
    MK = np.array(img.pixels[:], np.float32).reshape(H, W, 4)
uvb = bm.loops.layers.uv['UVMap']


def label(f):
    if MK is None or f[lh] or f[lk]:
        return '-'
    uv = sum((np.array(tuple(l[uvb].uv)) for l in f.loops)) / len(f.loops)
    m = MK[min(H - 1, int(uv[1] * H)), min(W - 1, int(uv[0] * W))]
    return 'RGBA'[int(np.argmax(m))] if m.max() > 0.3 else 'none'


rep = []
for lp in loops:
    vs = {v for x in lp for v in x.verts}
    P = np.array([tuple(mw @ v.co) for v in vs])
    c = P.mean(0)
    kinds = Counter('head' if x.link_faces[0][lh] else 'hand' if x.link_faces[0][lk] else 'body' for x in lp)
    bones = Counter(names[max(v[dl].items(), key=lambda kv: kv[1])[0]] if len(v[dl]) else '' for v in vs)
    rep.append({'edges': len(lp), 'centre': [round(float(x), 3) for x in c],
                'radius': round(float(np.linalg.norm(P - c, axis=1).mean()), 3), 'kind': dict(kinds),
                'bones': dict(bones.most_common(3)),
                'region': dict(Counter(label(x.link_faces[0]) for x in lp)),
                'z': [round(float(P[:, 2].min()), 3), round(float(P[:, 2].max()), 3)]})
rep.sort(key=lambda r: -r['edges'])
for r in rep:
    print('RIM', json.dumps(r))
if len(a) > 1:
    json.dump(rep, open(a[1], 'w'), indent=1)
