"""Texture quality pass (2026-10-30) for the 1K head set, without a new paint: the HeadUV that head_retexture_v1 was
painted on (Smart UV, 810 islands, 20 % of the atlas, 25 % of the head surface on fragments) is replaced by
claude_shared/uv_atlas.py charts; resample_head.py then carries Meshy's 2K head maps from the old layout into the new
one, so the face keeps its approved paint and gains the texels the 1K downsample used to throw away.

1. Head n-gons are triangulated (FIXED / EAR_CLIP: deterministic; loop UVs carried).
2. A copy holding only the head faces is unwrapped with one density, except the triangles the old layout made dense
   (the face skin, eyes and teeth islands at DENSE_RATIO x the hair): those charts are DENSE_FACTOR x denser, as
   measured on the old layout, so every region keeps its share of the Meshy source.
3. The new UVs replace HeadUV on the head faces; work/head_uv_texpass.npz keeps per head triangle (loop triangles of
   the new mesh) the old and new HeadUV and the rest xyz, for resample_head.py.

Args: -- <in blend (uv_texpass)> <out blend> <report json> [size=1024] [margin=2]
"""
import bpy, bmesh, sys, os, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
import uv_atlas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texpass_mesh import triangulate_head

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
opt = dict(a.split('=', 1) for a in argv[3:])
SIZE = int(opt.get('size', 1024))
MARGIN = int(opt.get('margin', 2))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data


rep = {'triangulated_head_ngons': triangulate_head(me)}
hd = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', hd)
tri = np.array([p.vertices[:] for p in me.polygons], dtype=object)
pos = np.array([v.co[:] for v in me.vertices])
old = np.zeros(len(me.loops) * 2, np.float32)
me.uv_layers['HeadUV'].data.foreach_get('uv', old)
old = old.reshape(-1, 2)
heads = np.nonzero(hd)[0]
otri = np.array([old[list(me.polygons[i].loop_indices)] for i in heads], np.float64)
ptri = np.array([pos[list(me.polygons[i].vertices)] for i in heads])
a3 = np.linalg.norm(np.cross(ptri[:, 1] - ptri[:, 0], ptri[:, 2] - ptri[:, 0]), axis=1) / 2
d1, d2 = otri[:, 1] - otri[:, 0], otri[:, 2] - otri[:, 0]
a2 = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / 2
ok = a3 > 1e-12
dens = np.where(ok, np.sqrt(a2 / np.maximum(a3, 1e-12)), 0)
kind = np.zeros(len(me.vertices), np.int32)
me.attributes['kind'].data.foreach_get('value', kind)
fk = np.array([np.bincount(kind[list(me.polygons[i].vertices)], minlength=5).argmax() for i in heads])


def wmed(x, w):
    o = np.argsort(x)
    c = np.cumsum(w[o])
    return float(x[o][np.searchsorted(c, c[-1] / 2)])


hair = (fk == 3) & ok
hair_med = wmed(dens[hair], a3[hair])
dense = ok & (dens > 2.0 * hair_med)
DENSE_FACTOR = wmed(dens[dense], a3[dense]) / hair_med
rep.update(hair_density_old=hair_med, dense_factor=DENSE_FACTOR, dense_surface_pct=float(100 * a3[dense].sum() / a3.sum()),
           dense_by_kind={int(k): int((dense & (fk == k)).sum()) for k in range(5)})

# ---- head-only copy with a vertex group marking the dense triangles
orig = me.attributes.new('orig_face', 'INT', 'FACE')
orig.data.foreach_set('value', np.arange(len(me.polygons), dtype=np.int32))
cp = body.copy()
cp.data = me.copy()
cp.modifiers.clear()
cp.parent = None
cp.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(cp)
bm = bmesh.new()
bm.from_mesh(cp.data)
of = bm.faces.layers.int['orig_face']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not hd[f[of]]], context='FACES')
bm.to_mesh(cp.data)
bm.free()
cme = cp.data
for g in list(cp.vertex_groups):
    if g.name == 'TexpassDense':
        cp.vertex_groups.remove(g)
grp = cp.vertex_groups.new(name='TexpassDense')
dense_faces = set(int(heads[i]) for i in np.nonzero(dense)[0])
cof = np.zeros(len(cme.polygons), np.int32)
cme.attributes['orig_face'].data.foreach_get('value', cof)
dverts = sorted({v for p in cme.polygons if int(cof[p.index]) in dense_faces for v in p.vertices})
grp.add(dverts, 1.0, 'REPLACE')
report = uv_atlas.unwrap(cp, head_groups=('TexpassDense',), head_factor=DENSE_FACTOR, size=SIZE, margin_px=MARGIN)
rep['uv_atlas'] = report
print('UV_ATLAS', json.dumps(report))
cuv = cme.uv_layers['UVMap'].data
table = {}
for p in cme.polygons:
    table[int(cof[p.index])] = {tuple(np.round(cme.vertices[v].co, 6)): tuple(cuv[li].uv)
                                for v, li in zip(p.vertices, p.loop_indices)}
huv = me.uv_layers['HeadUV'].data
newl = []
for i in heads:
    p = me.polygons[int(i)]
    t = table[int(i)]
    row = []
    for v, li in zip(p.vertices, p.loop_indices):
        huv[li].uv = t[tuple(np.round(me.vertices[v].co, 6))]
        row.append(huv[li].uv[:])
    newl.append(row)
bpy.data.objects.remove(cp)
me.attributes.remove(me.attributes['orig_face'])
me.uv_layers.active = me.uv_layers['UVMap']
np.savez(os.path.join(HERE, 'work', 'head_uv_texpass.npz'), old=otri.astype(np.float32),
         new=np.array(newl, np.float32), xyz=ptri.astype(np.float32), kind=fk.astype(np.int32))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('HEAD_TEXPASS', json.dumps({k: v for k, v in rep.items() if k != 'uv_atlas'}))
