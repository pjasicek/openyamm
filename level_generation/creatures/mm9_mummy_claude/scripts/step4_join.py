"""Join the cleaned head to the symmetric body at the neck, reduce the body by region (half, then mirrored), master-pose mesh `Body` with face attribute `head`.
Args: <body blend> <head blend> <out blend> <out npz>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
A, H, OUT, NPZ = sys.argv[sys.argv.index('--') + 1:]
SCALE, RING_Z, BODY_CUT = 0.43, 1.615, 1.60
bpy.ops.wm.open_mainfile(filepath=A)
ob = bpy.data.objects['Body']; me = ob.data
# reduce the body's left half by region
bm = bmesh.new(); bm.from_mesh(me)
g = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, BODY_CUT), plane_no=(0, 0, 1), clear_outer=True, clear_inner=False, dist=1e-5)
g = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, clear_inner=False, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.to_mesh(me); bm.free(); me.update()
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
def reduce(sel, ratio):
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='VERT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    C = np.array([tuple(v.co) for v in me.vertices]); m = sel(C)
    for i, v in enumerate(me.vertices): v.select = bool(m[i])
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.decimate(ratio=ratio); bpy.ops.object.mode_set(mode='OBJECT')
    print('REDUCE', int(m.sum()), len(me.polygons))
hand = lambda C: np.abs(C[:, 0]) > 0.47
foot = lambda C: C[:, 2] < 0.11
trunk = lambda C: (np.abs(C[:, 0]) <= 0.47) & (C[:, 2] >= 0.11)
print('START', len(me.polygons))
reduce(hand, 0.45); reduce(foot, 0.40); reduce(trunk, 0.55)
print('BODY HALF', len(me.polygons))
# neck tube: the body's neck goes up inside the hood, the hood's lower edge lies over it
bm = bmesh.new(); bm.from_mesh(me)
ring = [e for e in bm.edges if e.is_boundary and abs(e.verts[0].co.z - BODY_CUT) < 2e-3 and abs(e.verts[1].co.z - BODY_CUT) < 2e-3]
vs = list({v for e in ring for v in e.verts})
cy = (min(v.co.y for v in vs) + max(v.co.y for v in vs)) / 2
prev = {v: v for v in vs}
for dz, sc, sh in ((0.012, 0.88, 0.003), (0.030, 0.78, 0.009), (0.06, 0.74, 0.013), (0.11, 0.72, 0.013)):
    new = {v: bm.verts.new((v.co.x * sc, cy + sh + (v.co.y - cy) * sc, BODY_CUT + dz)) for v in vs}
    for e in ring:
        a_, b_ = e.verts
        bm.faces.new((prev[a_], prev[b_], new[b_], new[a_]))
    prev = new
bmesh.ops.triangulate(bm, faces=bm.faces)
for v in bm.verts:
    if abs(v.co.x) < 2e-4: v.co.x = 0
bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=3e-4)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
hl = bm.faces.layers.int.new('head')
# head
bb = bmesh.new()
with bpy.data.libraries.load(H) as (src, dst): dst.meshes = ['Head']
hm = dst.meshes[0]; bb.from_mesh(hm); bb.verts.ensure_lookup_table(); bb.faces.ensure_lookup_table()
ry = 0.048
print('HEAD RING y', ry, 'BODY y', cy)
vm = {v.index: bm.verts.new(((v.co.x) * SCALE, (v.co.y - ry) * SCALE + cy, (v.co.z + 0.165) * SCALE + RING_Z)) for v in bb.verts}
for f in bb.faces:
    try:
        nf = bm.faces.new([vm[v.index] for v in f.verts]); nf[hl] = 1
    except ValueError:
        print('DUP FACE')
bb.free()
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
co = np.array([tuple(v.co) for v in me.vertices])
T = np.array([tuple(p.vertices) for p in me.polygons]); H_ = np.zeros(len(T), np.int32); me.attributes['head'].data.foreach_get('value', H_)
np.savez(NPZ, co=co, tri=T, head=H_)
print('JOINED', len(co), len(T), H_.sum(), co.min(0), co.max(0))
