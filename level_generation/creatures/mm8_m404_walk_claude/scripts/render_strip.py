"""Render one clip of a creature GLB (with the sword on Socket_Sword) at evenly spaced phases, side and front.

Usage: blender -b -P render_strip.py -- <body.glb> <sword.glb> <clip> <out_dir> <tag> [n_frames]
Writes <out_dir>/<tag>_<view>_<k>.png (workbench, base-colour textures, orthographic)."""
import bpy, sys, os, math
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from glb_io import Glb
from gltf_pose import GltfPose, K, KI, node_matrix

a = sys.argv[sys.argv.index('--') + 1:]
body_glb, sword_glb, clip, out_dir, tag = a[:5]
n = int(a[5]) if len(a) > 5 else 8
os.makedirs(out_dir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=body_glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
gp = GltfPose(Glb(body_glb).json, rig)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=sword_glb)
sword = [o for o in set(bpy.data.objects) - before if o.parent is None]
sj = Glb(sword_glb).json
roots = {o: o.matrix_world.copy() for o in sword}
scene = bpy.context.scene
act = next(x for x in bpy.data.actions if x.name.split('|')[-1] == clip and x in [rig.animation_data.action] + list(bpy.data.actions))
rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
fps = scene.render.fps / scene.render.fps_base
dur = (act.frame_range[1] - act.frame_range[0]) / fps
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 360, 480
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new('w'); scene.world.color = (0.32, 0.33, 0.36)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.35
# floor line
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
floor = bpy.context.object
mat = bpy.data.materials.new('floor'); mat.diffuse_color = (0.18, 0.18, 0.2, 1); floor.data.materials.append(mat)
views = {'side': (Vector((4, 0.15, 0.95)), (math.radians(90), 0, math.radians(90))),
         'front': (Vector((0, -4, 0.95)), (math.radians(90), 0, 0))}
for k in range(n):
    t = dur * k / n
    f = act.frame_range[0] + t * fps
    scene.frame_set(int(f), subframe=f % 1); bpy.context.view_layer.update()
    G = rig.matrix_world @ rig.pose.bones['Socket_Sword'].matrix @ gp.C['Socket_Sword'].inverted()
    for o in sword:
        o.matrix_world = G @ roots[o]
    bpy.context.view_layer.update()
    for view, (loc, rot) in views.items():
        cam.location = loc; cam.rotation_euler = rot
        scene.render.filepath = os.path.join(out_dir, f'{tag}_{view}_{k}.png')
        bpy.ops.render.render(write_still=True)
print('RENDERED', tag, n, flush=True)
