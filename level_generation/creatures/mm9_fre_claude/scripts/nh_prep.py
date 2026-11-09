"""Pass 7 step A (Blender): Meshy Smart Topology head bust -> symmetric pieces in Fre's asm frame (metres, z up, front -y, MM9's mirrored
handedness: asm x = -true x).
- Pieces by size (work/nh/smart_raw.npz order): 0 face + neck + bust + skull, 1 hair shell, 3/4 eyeballs; the circlet wires, beads, jewel and
  the mouth inserts are dropped (the circlet is paint on the hair, as MM9's).
- Frame: eye midpoint and eye-line yaw/roll from the eyeball centroids; scale S (eye distance and eye-to-chin agree on 0.411); the eye
  midpoint goes to r72's (0, -0.0983, 0.6839) (r72 eyeball centroids; the chin and nose then sit 1 mm from r72's).
- Symmetry: the figure's right half (Meshy x < 0, the side the 3/4 master shows) is kept and mirrored (bisect at the eye midline, mirror,
  merge 0.2 mm), per piece, at full resolution (decimating one half tears the seam).
Output: work/nh/prep.npz (co, tri, piece: 0 face, 1 hair, 2 eyes). Args: <smart glb> <out npz>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
S = 0.411; EYE = np.array([0.0, -0.0983, 0.6839])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
o = next(x for x in bpy.data.objects if x.type == 'MESH')
for x in list(bpy.data.objects):
    if x is not o: bpy.data.objects.remove(x)
Mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Mw
bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data; me.materials.clear()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
P = np.array([v.co[:] for v in me.vertices]); n = len(P); par = np.arange(n)
def f(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for e in me.edges:
    a, b = f(e.vertices[0]), f(e.vertices[1]); par[a] = b
r = np.array([f(i) for i in range(n)]); u, inv, cnt = np.unique(r, return_inverse=True, return_counts=True)
rank = np.empty(len(u), int); rank[np.argsort(-cnt)] = np.arange(len(u)); comp = rank[inv]
eR, eL = P[comp == 4].mean(0), P[comp == 3].mean(0)          # x < 0 (kept side) and x > 0
print('EYES', eR.round(4), eL.round(4))
c = 0.5 * (eR + eL); d = eL - eR
yaw = np.arctan2(d[1], d[0]); roll = np.arctan2(d[2], np.hypot(d[0], d[1]))
print('YAW deg', round(float(np.degrees(yaw)), 3), 'ROLL deg', round(float(np.degrees(roll)), 3))
Q = P - c
cy, sy = np.cos(-yaw), np.sin(-yaw); Q = np.c_[Q[:, 0] * cy - Q[:, 1] * sy, Q[:, 0] * sy + Q[:, 1] * cy, Q[:, 2]]
cr, sr = np.cos(-roll), np.sin(-roll); Q = np.c_[Q[:, 0] * cr - Q[:, 2] * sr, Q[:, 1], Q[:, 0] * sr + Q[:, 2] * cr]
for v, p in zip(me.vertices, Q): v.co = Vector(p)
keep_sets = {'face': [0], 'hair': [1], 'eyes': [3, 4]}
out_co, out_tri, out_piece = [], [], []
for k, (name, cs) in enumerate(keep_sets.items()):
    d_ = o.copy(); d_.data = me.copy(); bpy.context.scene.collection.objects.link(d_)
    bm = bmesh.new(); bm.from_mesh(d_.data); bm.verts.ensure_lookup_table()
    keep = np.isin(comp, cs)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context='VERTS')
    # keep x < 0: clear_outer drops the +normal side
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
    for v in bm.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    for e in bm.edges:                                       # mirror seam: boundary vertices close to the plane go onto it
        if e.is_boundary:
            for v in e.verts:
                if abs(v.co.x) < 0.002: v.co.x = 0
    bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=2e-4)
    bmesh.ops.triangulate(bm, faces=[f_ for f_ in bm.faces if len(f_.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.verts.ensure_lookup_table(); bm.verts.index_update()
    co = np.array([v.co[:] for v in bm.verts]); tri = np.array([[v.index for v in f_.verts] for f_ in bm.faces])
    print('PIECE', name, len(co), len(tri), 'boundary', sum(1 for e in bm.edges if e.is_boundary), 'nonmanifold', sum(1 for e in bm.edges if len(e.link_faces) > 2))
    bm.free()
    out_tri.append(tri + sum(len(x) for x in out_co)); out_co.append(co); out_piece.append(np.full(len(co), k))
co = np.vstack(out_co); tri = np.vstack(out_tri); piece = np.concatenate(out_piece)
# Meshy (Blender axes, true-handed) -> asm: x negated (winding reversed), scaled, eye midpoint on r72's
co = np.c_[-co[:, 0], co[:, 1], co[:, 2]] * S + EYE; tri = tri[:, ::-1]
np.savez(OUT, co=co, tri=tri, comp=piece, piece=piece)
for k, nm in enumerate(keep_sets):
    q = co[piece == k]; print('ASM', nm, q.min(0).round(4), q.max(0).round(4))
