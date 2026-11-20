"""Head-only Meshy model -> bust. Spike off the chin removed, hidden inner walls deleted by ray visibility (Meshy doubles the hood), bust cut, shorter back and lower round
crown, left half mirrored, reduced with the face denser. Args: <glb> <out blend> <tris>"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
glb, OUT, TRIS = sys.argv[sys.argv.index('--') + 1:]; TRIS = int(TRIS)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
for o in list(bpy.context.scene.objects):
    if o is not ob: bpy.data.objects.remove(o)
me = ob.data; ob.parent = None; me.transform(ob.matrix_world); ob.matrix_world.identity(); me.materials.clear()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.105 and v.co.y < -0.115], context='VERTS')
g = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, -0.165), plane_no=(0, 0, -1), clear_outer=True, clear_inner=False, dist=1e-5)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.faces.ensure_lookup_table()
tree = BVHTree.FromBMesh(bm)
dirs = []
N = 180
for i in range(N):
    z = 1 - 2 * (i + .5) / N; r = math.sqrt(1 - z * z); a = i * 2.39996
    if z > -0.35 or (z > -0.75 and r * math.sin(a) < -0.2):     # never up through the open neck
        dirs.append(Vector((r * math.cos(a), r * math.sin(a), z)))
vis = set()
for f in bm.faces:
    c = f.calc_center_median()
    pts = [c] + [c.lerp(v.co, 0.7) for v in f.verts]
    done = False
    for p in pts:
        for d in dirs:
            o = p + d * 1.5
            hit = tree.ray_cast(o, -d, 2.0)
            if hit[0] is not None and hit[2] == f.index:
                done = True; break
            # two-sided: a ray from outside reaching this face first is what counts
        if done: break
    if done: vis.add(f.index)
print('VISIBLE', len(vis), 'of', len(bm.faces))
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in vis], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# keep shells of real size
bm.verts.ensure_lookup_table()
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); c = []
    while st:
        x = st.pop(); c.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
print('SHELLS', [len(c) for c in comps[:10]])
bmesh.ops.delete(bm, geom=[v for c in comps[1:] if len(c) < 60 for v in c], context='VERTS')
for v in bm.verts:
    x, y, z = v.co
    if y > 0.05: y = 0.05 + (y - 0.05) * 0.82
    if z > 0.20: z = 0.20 + (z - 0.20) * 0.84
    v.co = (x, y, z)
# hood crown and back onto a smooth ellipsoid (the Meshy crown is a lump), face and rim untouched
def sst(x, a, b):
    u = min(max((x - a) / (b - a), 0), 1); return u * u * (3 - 2 * u)
EC, ER = Vector((0, 0.02, 0.10)), Vector((0.235, 0.285, 0.27))
for v in bm.verts:
    d = v.co - EC
    if d.z <= 0 and d.y <= 0: continue
    e = Vector((d.x / ER.x, d.y / ER.y, d.z / ER.z))
    t = v.co * 0 + EC + d / max(e.length, 1e-6)
    w = max(sst(v.co.z, 0.12, 0.26), sst(v.co.y, 0.10, 0.20) * sst(v.co.z, -0.10, 0.02)) * sst(v.co.y, -0.22, -0.13)
    v.co = v.co.lerp(t, w)
g = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, -0.05, -0.165), plane_no=(0, 0.25, -1), clear_outer=True, clear_inner=False, dist=1e-5)
g = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, clear_inner=False, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.to_mesh(me); bm.free(); me.update()
print('HALF', len(me.polygons))
n = len(me.polygons)
vg = ob.vertex_groups.new(name='keep')
# hood: reduce hard; face: keep (weights 0 protect in the decimate modifier with invert off -> higher weight collapses first)
C = np.array([tuple(v.co) for v in me.vertices])
face = (C[:, 1] < -0.12) & (C[:, 2] > -0.135) & (C[:, 2] < 0.23)
vg.add(np.where(~face)[0].tolist(), 1.0, 'REPLACE')
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='VERT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for i, v in enumerate(me.vertices): v.select = bool(~face[i])
bpy.ops.object.mode_set(mode='EDIT')
nh = int((~face).sum()); bpy.ops.mesh.decimate(ratio=float(TRIS) * 0.22 / max(nh * 2, 1))
bpy.ops.object.mode_set(mode='OBJECT')
print('HOOD', n, len(me.polygons))
n = len(me.polygons)
if n > TRIS / 2 * 1.02:
    d = ob.modifiers.new('d', 'DECIMATE'); d.ratio = TRIS / 2 / n
    bpy.ops.object.modifier_apply(modifier='d')
print('FACE', len(me.polygons))
bm = bmesh.new(); bm.from_mesh(me)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
bmesh.ops.mirror(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], axis='X', merge_dist=2e-4)
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# the hole the spike left under the chin
adj = {}
for e in bm.edges:
    if e.is_boundary and e.verts[0].co.z < -0.08 and e.verts[0].co.y < -0.09 and e.verts[1].co.y < -0.09:
        adj[e] = True
print('CHIN EDGES', len(adj))
ret = bmesh.ops.holes_fill(bm, edges=list(adj), sides=64)
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
print('CHIN FILLED', len(ret['faces']))
# chin edge: the fill's jagged rim smoothed
ch = [v for v in bm.verts if -0.14 < v.co.z < -0.085 and v.co.y < -0.10]
for it in range(8):
    bmesh.ops.smooth_vert(bm, verts=ch, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
for pass_ in range(3):
    top = [e for e in bm.edges if e.is_boundary and e.verts[0].co.z > 0.2 and e.verts[1].co.z > 0.2]
    print('TOP EDGES', len(top))
    vs = list({v for e in top for v in e.verts})
    bmesh.ops.remove_doubles(bm, verts=vs, dist=0.02)
    top = [e for e in bm.edges if e.is_boundary and e.verts[0].co.z > 0.2 and e.verts[1].co.z > 0.2]
    if top: bmesh.ops.holes_fill(bm, edges=top, sides=200)
bmesh.ops.triangulate(bm, faces=bm.faces); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free(); me.update()
ob.name = 'Head'; me.name = 'Head'
for vg in list(ob.vertex_groups): ob.vertex_groups.remove(vg)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
co = np.array([tuple(v.co) for v in me.vertices])
print('HEAD', len(co), len(me.polygons), co.min(0), co.max(0))
