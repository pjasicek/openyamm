"""Rest-pose position of the surface under a pixel of a glb_close.py render (Standing frame 0).
Usage: blender -b -P pick_rest.py -- <glb> <bone> <ortho size> <dx,dy,dz view dir> <px> <py> [ox,oy,oz offset]  (420 px renders)"""
import sys, bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
glb, bone, size = a[0], a[1], float(a[2]); d = Vector([float(x) for x in a[3].split(',')]).normalized()
px, py = float(a[4]), float(a[5]); off = Vector([float(x) for x in a[6].split(',')]) if len(a) > 6 else Vector()
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb); sc = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); body = next(o for o in bpy.data.objects if o.type == 'MESH')
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
pb = rig.pose.bones[bone]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2) + off; cam = c + d * 5
q = (c - cam).to_track_quat('-Z', 'Y'); o = cam + (q @ Vector((1, 0, 0))) * (px / 420 - .5) * size + (q @ Vector((0, 1, 0))) * (.5 - py / 420) * size
b = bmesh.new(); b.from_object(body, bpy.context.evaluated_depsgraph_get()); b.transform(body.matrix_world)
hit = BVHTree.FromBMesh(b).ray_cast(o, q @ Vector((0, 0, -1)))
rig.animation_data.action = None
for p in rig.pose.bones:
    p.matrix_basis.identity()
bpy.context.view_layer.update(); r = bmesh.new(); r.from_object(body, bpy.context.evaluated_depsgraph_get()); r.transform(body.matrix_world)
r.faces.ensure_lookup_table(); f = r.faces[hit[2]]
print('REST', ','.join(f'{x:.3f}' for x in sum((v.co for v in f.verts), Vector()) / 3))
