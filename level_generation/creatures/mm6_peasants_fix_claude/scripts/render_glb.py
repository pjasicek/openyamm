"""Textured EEVEE renders of an actor GLB at one clip frame (review only). Back faces culled as the engine draws them.
Env: CLIP (Standing; REST = bind pose), FRAME (0), VIEWS ('f:0,back:180,side:90': name:angle around the actor, 0 = its front),
DIST (m), DZ (m, aim height over the neck), RES (px, square). Args: -- <glb> <out prefix>"""
import bpy, sys, os, math
from mathutils import Vector
glb, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
for m in bpy.data.materials:
    m.use_backface_culling = True
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
clip = os.environ.get('CLIP', 'Standing')
if clip == 'REST':                                    # the bind pose
    arm.animation_data_create(); arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
else:
    act = next(a for a in bpy.data.actions if a.name.split('|')[-1] == clip or a.name == clip)
    arm.animation_data.action = act
    if len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
sc = bpy.context.scene; sc.frame_set(int(os.environ.get('FRAME', '0')))
W = arm.matrix_world
neck = next(b.name for b in arm.pose.bones if b.name.endswith('Neck'))
hz = (W @ arm.pose.bones[neck].head).z
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True
bg = sc.world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.6, 0.62, 0.65, 1); bg.inputs[1].default_value = 0.7
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(50), 0, math.radians(30))
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('RES', '500'))
D = float(os.environ.get('DIST', '1.6')); DZ = float(os.environ.get('DZ', '-0.12'))
for item in os.environ.get('VIEWS', 'f:0,back:180,side:90').split(','):
    name, ang = item.split(':'); an = math.radians(float(ang))
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 85; t = Vector((W.translation.x, W.translation.y, hz + DZ))
    cam.location = t + Vector((math.sin(an) * D, -math.cos(an) * D, 0.12 * D / 1.1))
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{name}.png'; bpy.ops.render.render(write_still=True)
