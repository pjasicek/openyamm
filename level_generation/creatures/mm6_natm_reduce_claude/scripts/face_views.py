"""Face, torso and spear-hand renders of a natm runtime GLB (Standing frame 0, EEVEE, the party side = -Y):
<out>/<label>_{face_front,face_q34,torso,hand}.png. Args: -- <glb> <label> <out dir>"""
import bpy, sys, os, math
from mathutils import Vector
glb, label, out = sys.argv[sys.argv.index('--') + 1:][:3]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions['Standing']
if len(bpy.data.actions['Standing'].slots): rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
sc.frame_set(0)
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 600
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (0.55, 0.6, 0.66, 1); bg.inputs[1].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
P = lambda n: rig.matrix_world @ rig.pose.bones[n].head
head = P('B_Head') + Vector((0, 0, 0.08)); hand = P('B_R_Hand'); chest = P('B_Spine2')
shots = {'face_front': (head + Vector((0, -0.75, 0.02)), head), 'face_q34': (head + Vector((-0.5, -0.55, 0.05)), head),
         'torso': (chest + Vector((0.35, -1.6, 0.1)), chest + Vector((0, 0, -0.1))), 'hand': (hand + Vector((-0.35, -0.45, 0.15)), hand),
         'chest': (chest + Vector((0.0, -1.05, 0.0)), chest + Vector((0, 0, -0.12)))}
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
for k, (p, t) in shots.items():
    cam.location = p; cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out, f'{label}_{k}.png'); bpy.ops.render.render(write_still=True)
print('FACEVIEWS', label)
