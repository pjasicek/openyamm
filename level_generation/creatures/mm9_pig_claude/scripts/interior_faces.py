"""Find (and optionally delete) hidden interior faces: a face is interior when every one of N rays cast from just
above its centre into its normal hemisphere hits the mesh again within REACH (it can never be seen from outside).
Args: <blend|glb> <object or -> [out blend] [reach] ; with out blend the interior faces of 'Body' are deleted
(vertex groups and attributes kept), loose vertices removed."""
import bpy, bmesh, sys, math, random
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
src, name = argv[0], argv[1]
out = argv[2] if len(argv) > 2 and argv[2] != '-' else None
REACH = float(argv[3]) if len(argv) > 3 else 5.0
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
ob = bpy.data.objects[name] if name != '-' else next(o for o in bpy.data.objects if o.type == 'MESH')
for rig in (o for o in bpy.data.objects if o.type == 'ARMATURE'):
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
bvh = BVHTree.FromBMesh(bm)
rng = random.Random(1)
dirs = []
for k in range(24):
    z = rng.random() * 0.95 + 0.05
    phi = rng.random() * 2 * math.pi
    r = math.sqrt(1 - z * z)
    dirs.append(Vector((r * math.cos(phi), r * math.sin(phi), z)))
interior = []
for f in bm.faces:
    n = f.normal
    if n.length < 1e-9:
        continue
    t = n.orthogonal().normalized(); b = n.cross(t)
    o = f.calc_center_median() + n * 1e-4
    blocked = True
    for d in dirs:
        w = t * d.x + b * d.y + n * d.z
        hit = bvh.ray_cast(o, w, REACH)
        if hit[0] is None:
            blocked = False
            break
    if blocked:
        interior.append(f)
area = sum(f.calc_area() for f in interior); total = sum(f.calc_area() for f in bm.faces)
print('INTERIOR', len(interior), 'of', len(bm.faces), 'faces; area %.3f of %.3f' % (area, total))
if out:
    bmesh.ops.delete(bm, geom=interior, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(ob.data)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print('SAVED', out, len(ob.data.polygons))
