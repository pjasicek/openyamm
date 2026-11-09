"""Clean voxel body -> game mesh: Laplacian smoothing (removes the 1 mm voxel ripple), collapse decimation to
BODY_TRIS, exact mirror symmetry (the -x half rebuilt from the +x half, merged on x = 0), triangulated; the eyes
decimated to EYE_TRIS each and joined into 'Body' (face attribute 'piece' 1 = eye). Fins are untouched.
Args: <in blend> <out blend> [body_tris=3600] [eye_tris=96]"""
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = argv[0], argv[1]
BODY_TRIS = int(argv[2]) if len(argv) > 2 else 3600
EYE_TRIS = int(argv[3]) if len(argv) > 3 else 96
bpy.ops.wm.open_mainfile(filepath=IN)
body, eyes = bpy.data.objects['Body'], bpy.data.objects['Eyes']


def apply(ob, mod):
    bpy.context.view_layer.objects.active = ob
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.ops.object.modifier_apply(modifier=mod.name)


m = body.modifiers.new('ls', 'LAPLACIANSMOOTH'); m.iterations = 6; m.lambda_factor = 0.6; m.use_volume_preserve = True
apply(body, m)
# keep the +x half, decimate it, mirror it back
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0),
                       clear_inner=True)
for v in bm.verts:
    if abs(v.co.x) < 1e-6:
        v.co.x = 0.0
bm.to_mesh(body.data); bm.free()
tris_half = sum(len(p.vertices) - 2 for p in body.data.polygons)
m = body.modifiers.new('dec', 'DECIMATE'); m.ratio = (BODY_TRIS / 2) / max(tris_half, 1); m.use_symmetry = False
apply(body, m)
bm = bmesh.new(); bm.from_mesh(body.data)
for v in bm.verts:
    if abs(v.co.x) < 2e-4:
        v.co.x = 0.0
bm.to_mesh(body.data); bm.free()
m = body.modifiers.new('mir', 'MIRROR'); m.use_axis[0] = True; m.use_mirror_merge = True; m.merge_threshold = 1e-5
apply(body, m)
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(body.data); bm.free()
# eyes: the Meshy eye pieces are small sunk bumps; a clean glossy lens replaces them: a sphere of EYE_R at the Meshy
# eye centre, pushed out so it stands EYE_OUT proud of the head surface (the MM9 fish has a large golden eye)
from mathutils.bvhtree import BVHTree
from mathutils import Vector
EYE_R, EYE_OUT = 0.0058, 0.0022
ev = [eyes.matrix_world @ v.co for v in eyes.data.vertices if v.co.x > 0]
c = sum(ev, Vector()) / len(ev)
tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
hit = tree.ray_cast(Vector((0.08, c.y, c.z)), Vector((-1, 0, 0)))
surf_x = hit[0].x if hit[0] else c.x
centre = Vector((surf_x - EYE_R + EYE_OUT, c.y, c.z))
bpy.data.objects.remove(eyes)
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=9, radius=EYE_R)
bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(1.5708, 3, 'Y'))
bmesh.ops.translate(bm, verts=bm.verts, vec=centre)
mir = bm.copy()
for v in mir.verts:
    v.co.x = -v.co.x
bmesh.ops.reverse_faces(mir, faces=mir.faces)
tmp = bpy.data.meshes.new('t'); mir.to_mesh(tmp); bm.from_mesh(tmp)
bmesh.ops.triangulate(bm, faces=bm.faces)
me_e = bpy.data.meshes.new('Eyes'); bm.to_mesh(me_e); bm.free()
eyes = bpy.data.objects.new('Eyes', me_e); bpy.context.scene.collection.objects.link(eyes)
print('EYE centre', tuple(round(x, 4) for x in centre), 'surface x', round(surf_x, 4))
pa = body.data.attributes.new('piece', 'INT', 'FACE')
pe = eyes.data.attributes.new('piece', 'INT', 'FACE')
for d in pe.data:
    d.value = 1
for o in bpy.data.objects:
    o.select_set(o in (body, eyes))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
for p in body.data.polygons:
    p.use_smooth = True
n_body = sum(1 for p in body.data.polygons)
xs = [v.co.x for v in body.data.vertices]
print('REDUCED', n_body, 'tris', 'xrange', min(xs), max(xs))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
