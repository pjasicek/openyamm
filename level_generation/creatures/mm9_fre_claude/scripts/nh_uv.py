"""Pass 7 step C (Blender): head-set UVs for the new head with claude_shared/uv_atlas.py (xatlas charts, small charts merged, one density,
brute-force packing, 2 px margin at 1024). Density classes: the face front (eyes, nose, mouth, cheeks) x FACE_K; hidden surfaces x HID_K
(the skull under the hair: its outward ray and four rays tilted 18 deg all hit the hair; the hair's inward faces on the top, z > 0.70).
Never re-run once the upload went to Meshy (xatlas packs differently per run): the paint belongs to work/nh/head_uv.npz.
Output npz: co, tri, uv (vertices split at UV seams), src (head_geo vertex per output vertex), and the upload GLB (true-handed: x
negated, glTF axes, neutral, no material). Args: <head_geo npz> <out npz> <upload glb>"""
import bpy, bmesh, sys, os, json, struct
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'claude_shared')); import uv_atlas
IN, OUT, UP = sys.argv[sys.argv.index('--') + 1:]
E = os.environ.get; FACE_K = float(E('FACE_K', '2.0')); HID_K = float(E('HID_K', '0.3'))
D = np.load(IN); co, tri, pc, fp = D['co'], D['tri'], D['piece'], D['fpiece']
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('NewHead'); me.from_pydata(co.tolist(), [], tri.tolist()); me.update()
o = bpy.data.objects.new('NewHead', me); bpy.context.scene.collection.objects.link(o); bpy.context.view_layer.objects.active = o
ht = tri[fp == 1]; bvh = BVHTree.FromPolygons([Vector(p) for p in co], ht.tolist())
C = Vector((0, 0.005, 0.69))
cen = co[tri].mean(1); fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
hidden = np.zeros(len(tri), bool); face = np.zeros(len(tri), bool)
for f in range(len(tri)):
    c = Vector(cen[f])
    if fp[f] == 1:
        hidden[f] = (Vector(fn[f]).dot(c - C) < 0) and cen[f, 2] > 0.70
        continue
    if fp[f] not in (0,): continue
    d0 = (c - C).normalized(); ok = True
    t1 = d0.orthogonal().normalized(); t2 = d0.cross(t1)
    for d in (d0, (d0 + 0.32 * t1).normalized(), (d0 - 0.32 * t1).normalized(), (d0 + 0.32 * t2).normalized(), (d0 - 0.32 * t2).normalized()):
        hit = bvh.ray_cast(c + d * 1e-4, d, 0.2)
        if hit[0] is None: ok = False; break
    hidden[f] = ok
    face[f] = (not ok) and cen[f, 1] < -0.05 and 0.585 < cen[f, 2] < 0.73 and abs(cen[f, 0]) < 0.06
face |= fp == 2
print('UV classes: hidden', int(hidden.sum()), 'face', int(face.sum()), 'of', len(tri))
for name, sel in (('Hidden', hidden), ('Face', face)):
    g = o.vertex_groups.new(name=name); vs = np.unique(tri[sel])
    # a vertex belongs when all its faces do (uv_atlas averages vertex weights per face)
    cnt = np.bincount(tri.ravel(), minlength=len(co)); cs = np.bincount(tri[sel].ravel(), minlength=len(co))
    full = np.where((cs == cnt) & (cnt > 0))[0]
    if len(full): g.add(full.tolist(), 1.0, 'REPLACE')
rep = uv_atlas.unwrap(o, size=int(E('UV_SIZE', '1024')), margin_px=2, max_cost=float(E('UV_COST', '2.0')), group_factors={'Face': FACE_K, 'Hidden': HID_K})
print('UV_ATLAS', json.dumps(rep))
json.dump(rep, open(OUT.replace('.npz', '_report.json'), 'w'), indent=1)
if E('FACE_ONE', '0') == '1':      # tried, not used: minimum stretch p90 4.2, conformal collapsed 31 triangles
    # the face front (eyes, nose, mouth, cheeks) as ONE island: xatlas cut it into ~20 charts and Meshy's paint draws lines along
    # chart seams (r6-r20 cheek line); Blender's minimum-stretch unwrap of just those faces, scaled to their uv_atlas density, then
    # every island is packed again by uv_atlas's xatlas packer
    F = np.where(face & (fp == 0))[0]; Fs = set(F.tolist())
    def corners():
        Lc = me.uv_layers['UVMap'].data
        return np.array([[Lc[li].uv[:] for li in p.loop_indices] for p in me.polygons])
    uv0 = corners(); p3 = co[tri]
    a3 = np.linalg.norm(np.cross(p3[:, 1] - p3[:, 0], p3[:, 2] - p3[:, 0]), axis=1) / 2
    def a2of(u): return np.abs((u[:, 1, 0] - u[:, 0, 0]) * (u[:, 2, 1] - u[:, 0, 1]) - (u[:, 2, 0] - u[:, 0, 0]) * (u[:, 1, 1] - u[:, 0, 1])) / 2
    dens = np.sqrt(a2of(uv0[F]).sum() / a3[F].sum())
    bpy.ops.object.mode_set(mode='EDIT'); bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
    for e in bm.edges:
        lf = [f.index in Fs for f in e.link_faces]; e.seam = any(lf) and not all(lf)
    for f in bm.faces: f.hide_set(f.index not in Fs); f.select_set(f.index in Fs)
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.unwrap(method=E('FACE_METHOD', 'ANGLE_BASED'), margin=0.0)
    bm = bmesh.from_edit_mesh(me)
    for f in bm.faces: f.hide_set(False)
    bmesh.update_edit_mesh(me); bpy.ops.object.mode_set(mode='OBJECT')
    uv1 = corners(); s_ = dens / np.sqrt(a2of(uv1[F]).sum() / a3[F].sum()); c_ = uv1[F].reshape(-1, 2).mean(0)
    uv1[F] = c_ + (uv1[F] - c_) * s_ + 5.0          # out of the way of the other islands before packing
    flip = a2of(uv1[F]); print('FACE ONE island', len(F), 'faces; density kept', round(float(dens), 4))
    packed = uv_atlas._xatlas('pack', {'uv': uv1.astype(np.float32), 'vert': tri.astype(np.int32)}, '--size', int(E('UV_SIZE', '1024')), '--padding', 2,
                              '--height-share', 1.0, '--fine', 0, '--steps', 10)['uv']
    Lc = me.uv_layers['UVMap'].data
    for pi, p in enumerate(me.polygons):
        for k_, li in enumerate(p.loop_indices): Lc[li].uv = packed[pi, k_]
L = me.uv_layers['UVMap'].data
key = {}; nco, nuv, nsrc, ntri = [], [], [], []
for p in me.polygons:
    t = []
    for li, vi in zip(p.loop_indices, p.vertices):
        u = L[li].uv; k = (vi, round(u[0], 6), round(u[1], 6))
        if k not in key: key[k] = len(nco); nco.append(co[vi]); nuv.append((u[0], u[1])); nsrc.append(vi)
        t.append(key[k])
    ntri.append(t)
nco, nuv, nsrc, ntri = np.array(nco), np.array(nuv), np.array(nsrc), np.array(ntri)
np.savez(OUT, co=nco, tri=ntri, uv=nuv, src=nsrc, fpiece=fp, hidden=hidden, face=face)
print('UV split verts', len(nco), 'faces', len(ntri))
# upload glb: true-handed (x negated), Blender -> glTF axes, winding reversed by the mirror
P = np.c_[-nco[:, 0], nco[:, 2], -nco[:, 1]].astype('f4'); T = ntri[:, ::-1].astype('u4'); UV = (nuv * [1, -1] + [0, 1]).astype('f4')
fn2 = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
k5 = np.round(P, 5); _, inv = np.unique(k5, axis=0, return_inverse=True); inv = inv.ravel(); Ns = np.zeros((inv.max() + 1, 3))
for c in range(3): np.add.at(Ns, inv[T[:, c]], fn2)
N = Ns[inv]; N = (N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)).astype('f4')
blob = bytearray(); views = []; accs = []
def add(a, ct, ty, tg, mm=False):
    while len(blob) % 4: blob.append(0)
    o_ = len(blob); b = a.tobytes(); blob.extend(b); views.append({'buffer': 0, 'byteOffset': o_, 'byteLength': len(b), 'target': tg})
    x = {'bufferView': len(views) - 1, 'componentType': ct, 'count': len(a), 'type': ty}
    if mm: x['min'] = a.min(0).tolist(); x['max'] = a.max(0).tolist()
    accs.append(x); return len(accs) - 1
pa = add(P, 5126, 'VEC3', 34962, True); na = add(N, 5126, 'VEC3', 34962); ua = add(UV, 5126, 'VEC2', 34962); ia = add(T.ravel(), 5125, 'SCALAR', 34963)
doc = {'asset': {'version': '2.0', 'generator': 'mm9_fre nh_uv'}, 'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'name': 'FreNewHead', 'mesh': 0}],
       'meshes': [{'name': 'FreNewHead', 'primitives': [{'attributes': {'POSITION': pa, 'NORMAL': na, 'TEXCOORD_0': ua}, 'indices': ia, 'mode': 4}]}],
       'accessors': accs, 'bufferViews': views, 'buffers': [{'byteLength': len(blob)}]}
j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
while len(blob) % 4: blob.append(0)
doc['buffers'][0]['byteLength'] = len(blob); j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
os.makedirs(os.path.dirname(UP), exist_ok=True)
with open(UP, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(blob))); f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j)
    f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
print('UPLOAD', UP, len(P), len(T))
