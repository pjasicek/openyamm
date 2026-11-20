"""Side-view filmstrip of Walking viewer frames (48 fps) from a GLB: fixed ortho camera from the character's left,
textured, a floor line and a red line at the head height of the first frame, so a height jump reads directly.
Usage: blender -b -P walk_filmstrip.py -- <glb> <label> [first last] -> review/walk/<label>_fNN.png"""
import math, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; glb, label = a[:2]; f0, f1 = (int(a[2]), int(a[3])) if len(a) > 3 else (10, 20)
out = os.path.join(HERE, 'review', 'walk'); os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 48
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.animation_data.action = bpy.data.actions['Walking']
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.9
c = Vector((0, 0, .9)); cam.location = c + Vector((3, 0, 0)); cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(45), 0, math.radians(60))
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)


def bar(name, z, col, thick=.003):
    me = bpy.data.meshes.new(name); me.from_pydata([(0.4, -1, z - thick), (0.4, 1, z - thick), (0.4, 1, z + thick), (0.4, -1, z + thick)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = col; nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface']); me.materials.append(m)


sc.frame_set(f0); head0 = (rig.matrix_world @ rig.pose.bones['B_Head'].head).z
bar('Floor', 0, (0, 0, 0, 1)); bar('Ref', head0, (1, 0, 0, 1), .002)
sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = 260, 520
for f in range(f0, f1 + 1):
    sc.frame_set(f); sc.render.filepath = os.path.join(out, f'{label}_f{f:02d}.png'); bpy.ops.render.render(write_still=True)
print('FILM', label, f0, f1, 'ref head %.4f' % head0)
