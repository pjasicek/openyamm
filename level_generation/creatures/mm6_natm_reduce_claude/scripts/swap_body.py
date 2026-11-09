"""Put the picked reduction (work/mesh_<step>.npz, MeshLab texture-aware quadric) into the cannibal's gated master
(../mm6_natm_claude/work/rig_v5.blend: rig, final clips, weights, per-vertex piece/garment/finger/orig_co) for a fresh
Meshy retexture. The npz is in the same rest frame as the master's Body (Z up, metres).

Per connected piece of the reduced mesh: the source piece by majority of nearest source vertices (labels per piece,
never per vertex: per-vertex labels mixed skin and feather cards). Each vertex then takes weights and orig_co by
barycentric interpolation on the nearest source triangle of that piece, and its piece/garment/finger labels from the
nearest corner. Weights are normalised; the reduced mesh carries no UVs (the body upload takes Meshy's own layout).
Writes work/rig_v5.blend. Args: -- <step, e.g. r55>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
step = sys.argv[sys.argv.index('--') + 1]
d = np.load(os.path.join(HERE, 'work', f'mesh_{step}.npz'))
V, F = d['verts'], d['faces'].astype(np.int64)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm6_natm_claude', 'work', 'rig_v5.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()

S = np.array([tuple(v.co) for v in me.vertices])
ST = np.array([[p.vertices[0], p.vertices[i], p.vertices[i + 1]] for p in me.polygons for i in range(1, len(p.vertices) - 1)])
lab = {}
for n in ('piece', 'garment', 'finger'):
    a = np.zeros(len(S), np.int32); me.attributes[n].data.foreach_get('value', a); lab[n] = a
oc = np.zeros(len(S) * 3); me.attributes['orig_co'].data.foreach_get('vector', oc); oc = oc.reshape(-1, 3)
G = len(body.vertex_groups)
W = np.zeros((len(S), G))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight

# labels per FACE: the reduction's source was welded (glTF import), which joins pendants and hip-trim cards to the skin,
# so a per-component vote labelled whole pendants skin (h65 review: peach pendant strips on the chest). Each reduced
# face takes the piece of the nearest source triangle within 12 mm whose normal agrees (dot > 0.3), else the nearest.
SN = np.cross(S[ST[:, 1]] - S[ST[:, 0]], S[ST[:, 2]] - S[ST[:, 0]])
SN /= np.maximum(np.linalg.norm(SN, axis=1, keepdims=True), 1e-12)
bvh_all = BVHTree.FromPolygons([Vector(x) for x in S], ST.tolist(), all_triangles=True)
FC = V[F].mean(1); FN = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
FA = np.linalg.norm(FN, axis=1) / 2; FN /= np.maximum(2 * FA[:, None], 1e-12)
tri_piece = lab['piece'][ST[:, 0]]
fpiece = np.zeros(len(F), np.int32); nflip = 0
for fi in range(len(F)):
    cands = bvh_all.find_nearest_range(Vector(FC[fi]), 0.012)
    good = [c for c in cands if SN[c[2]] @ FN[fi] > 0.3]
    if good:
        ti = min(good, key=lambda c: c[3])[2]
    else:
        ti = bvh_all.find_nearest(Vector(FC[fi]))[2]; nflip += 1
    fpiece[fi] = tri_piece[ti]
gar_of_piece = {}
for pc in np.unique(lab['piece']):
    vals, cnt = np.unique(lab['garment'][lab['piece'] == pc], return_counts=True); gar_of_piece[pc] = vals[cnt.argmax()]
fgar = np.array([gar_of_piece[pc] for pc in fpiece], np.int32)
# vertex piece = area-weighted majority of its faces; weights from the nearest source triangle of that piece
vote = {}
for fi, f in enumerate(F):
    for v in f:
        vote.setdefault(v, {}); vote[v][fpiece[fi]] = vote[v].get(fpiece[fi], 0) + FA[fi]
vpiece = np.array([max(vote[i].items(), key=lambda x: x[1])[0] if i in vote else 0 for i in range(len(V))], np.int32)
bvh = {}
for pc in np.unique(vpiece):
    idx = np.where(tri_piece == pc)[0]
    bvh[pc] = (BVHTree.FromPolygons([Vector(x) for x in S], ST[idx].tolist(), all_triangles=True), idx)
src_piece = set(fpiece.tolist())

NW = np.zeros((len(V), G)); NOC = np.zeros((len(V), 3)); NL = {n: np.zeros(len(V), np.int32) for n in lab}
far = 0.0; nfb = 0
for i, p in enumerate(V):
    pc = vpiece[i]; tree, idx = bvh[pc]
    loc, _, ti, dist = tree.find_nearest(Vector(p))
    if dist > 0.005:
        tree, idx = bvh_all, np.arange(len(ST)); loc, _, ti, dist = tree.find_nearest(Vector(p)); nfb += 1
    far = max(far, dist)
    t = ST[idx[ti]]
    A, B, C = S[t]; P = np.array(loc)
    v0, v1, v2 = B - A, C - A, P - A
    d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    if den < 1e-18:
        bc = np.array([1.0, 0, 0])
    else:
        y = (d11 * d20 - d01 * d21) / den; z = (d00 * d21 - d01 * d20) / den; bc = np.clip([1 - y - z, y, z], 0, 1)
        bc /= bc.sum()
    NW[i] = bc @ W[t]; NOC[i] = bc @ oc[t]
    k = t[np.argmax(bc)]
    for n in lab:
        NL[n][i] = lab[n][k]
    NL['piece'][i] = pc; NL['garment'][i] = gar_of_piece[pc]
NW /= np.maximum(NW.sum(1, keepdims=True), 1e-9)

nm = bpy.data.meshes.new('Body')
nm.from_pydata(V.tolist(), [], F.tolist()); nm.update()
for n in lab:
    nm.attributes.new(n, 'INT', 'POINT').data.foreach_set('value', NL[n].tolist())
nm.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', NOC.ravel().tolist())
nm.attributes.new('fgarment', 'INT', 'FACE').data.foreach_set('value', fgar.tolist())   # uv_raster labels texels by face
nm.attributes.new('fpiece', 'INT', 'FACE').data.foreach_set('value', fpiece.tolist())
old = me
gnames = [g.name for g in body.vertex_groups]   # group names live on the mesh: recreate them on the new one
body.data = nm
for gi, name in enumerate(gnames):
    g = body.vertex_groups.new(name=name); col = NW[:, gi]
    for vi in np.where(col > 1e-4)[0]:
        g.add([int(vi)], float(col[vi]), 'REPLACE')
bpy.data.meshes.remove(old)
for p in nm.polygons:
    p.use_smooth = True
print('SWAP', step, 'tris', len(F), 'verts', len(V), 'pieces', len(src_piece), 'of source', len(np.unique(lab['piece'])),
      'max surface distance mm', round(far * 1000, 1), 'fallback vertices', nfb, 'faces without a normal match', nflip,
      'face garments', {int(k): int(c) for k, c in zip(*np.unique(fgar, return_counts=True))})
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v5.blend'))
