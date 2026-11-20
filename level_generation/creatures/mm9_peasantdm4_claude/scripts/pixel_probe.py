"""Which face and texel does a pixel of a closeup.py view show? (diagnostic, PeasantDM4 sleeve patch, 2026-11-02)
Args (Blender): <glb> <clip|bind> <frame30> <bone> <az> <el> <ortho> <px,py> [px,py ...]   (512 px image, origin top left)
Prints material, face index, UV (glTF v down) and the texel colour of the base colour image."""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
GLB, clip, f30, bone, az, el, ortho = a[0], a[1], int(a[2]), a[3], float(a[4]), float(a[5]), float(a[6])
pix = [tuple(float(v) for v in s.split(',')) for s in a[7:]]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and 'LOD' not in o.name and 'Shadow' not in o.name)
sc = bpy.context.scene; FPS = sc.render.fps / sc.render.fps_base
rig.animation_data_create()
if clip != 'bind':
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
    fr = act.frame_range[0] + f30 / 30.0 * FPS; sc.frame_set(int(fr), subframe=fr % 1.0)
bpy.context.view_layer.update()
T = rig.matrix_world @ rig.pose.bones[bone].head
d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
fwd = -d; right = fwd.cross(Vector((0, 0, 1))).normalized(); up = right.cross(fwd).normalized()
dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); me = ev.to_mesh()
from mathutils.bvhtree import BVHTree
M = mesh.matrix_world
verts = [M @ v.co for v in me.vertices]
polys = [list(p.vertices) for p in me.polygons]
bvh = BVHTree.FromPolygons(verts, polys)
uvl = me.uv_layers.active.data
for px, py in pix:
    o = T + right * ((px / 512 - 0.5) * ortho) + up * ((0.5 - py / 512) * ortho) + d * 4.0
    loc, nrm, fi, dist = bvh.ray_cast(o, fwd)
    if fi is None:
        print('PIXPROBE', px, py, 'miss'); continue
    p = me.polygons[fi]
    mat = mesh.material_slots[p.material_index].material
    uv = sum((uvl[li].uv for li in p.loop_indices), Vector((0, 0))) / len(p.loop_indices)
    img = None
    for n in mat.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and 'Base' in ''.join(l.to_socket.name for l in n.outputs[0].links):
            img = n.image
    col = None
    if img:
        W, H = img.size; x = int(uv.x * W) % W; y = int(uv.y * H) % H
        i = (y * W + x) * 4; col = [round(c * 255) for c in img.pixels[i:i + 3]]
    print('PIXPROBE', px, py, 'mat', mat.name, 'face', fi, 'uv(blender v up)', [round(uv.x, 4), round(uv.y, 4)], 'texel', col, 'normal.dot(view)', round(nrm.dot(-fwd), 2))
