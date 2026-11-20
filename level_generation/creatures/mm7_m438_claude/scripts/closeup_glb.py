"""Textured close-ups (EEVEE, perspective) of the right-arm stump and the held forearm's cut end from a viewer tier GLB
(review/viewer/mm7_m438_<tier>.glb: the tier's ramps baked), Standing frame 15: front and three-quarter cameras aimed
at the stump end (B_R_Forearm head + 12 cm along the forearm) and at the prop's club end ('Sword' bone + 19 cm along
its +Y). Writes <out prefix>_{stump,prop}_{front,tq}.png. Args: -- <glb> <out prefix>"""
import bpy, sys, os, math
from mathutils import Vector
glb, outp = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = next(x for x in bpy.data.actions if x.name.split('|')[-1] == 'Standing' or x.name == 'Standing')
arm.animation_data.action = act
if len(act.slots): arm.animation_data.action_slot = act.slots[0]
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 520, 520
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.55, 0.6, 0.66, 1); bg.inputs[1].default_value = 1.0
for loc, e in (((2, -3, 4), 3.0), ((-3, -2, 2), 1.5), ((0, 3, 3), 1.0)):
    l = bpy.data.lights.new('l', 'SUN'); l.energy = e; o = bpy.data.objects.new('l', l); sc.collection.objects.link(o)
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
sc.frame_set(15)
M = arm.matrix_world
fa = M @ arm.pose.bones['B_R_Forearm'].matrix; stump = fa.translation + (fa.to_3x3() @ Vector((0, 1, 0))).normalized() * 0.12
sw = M @ arm.pose.bones['Sword'].matrix; prop = sw.translation + (sw.to_3x3() @ Vector((0, 1, 0))).normalized() * 0.19
cd = bpy.data.cameras.new('c'); cd.lens = 85; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
fwd = (M.to_3x3() @ Vector((0, 0, 1))).normalized()          # glTF +Z front, imported as Blender -Y
for name, tgt in (('stump', stump), ('prop', prop)):
    for vn, yaw in (('front', 0), ('tq', 40)):
        d = Vector((math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)), 0.12)).normalized()
        cam.location = tgt + d * 0.9
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{outp}_{name}_{vn}.png'
        bpy.ops.render.render(write_still=True)
print('CLOSEUPS', outp)
