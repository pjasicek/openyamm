# Blender: first-person look checks of the installed MM8 Dragon (mm8_m492) for the solo-mode Dragon.
# blender -b --python render_fp.py -- <mm8_m492.glb> <out_dir>
# Renders: eye view standing (what the snout shows), eye view with the forelimbs posed into view by IK (a swipe), and a
# close third-person view of a forefoot (texture density at first-person distance). Private check, no game asset made.
import bpy, sys, math, mathutils
args = sys.argv[sys.argv.index('--') + 1:]
src, out = args[0], args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.render.film_transparent = False
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.68, 0.85, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.8
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.animation_data.action = bpy.data.actions['Standing']
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body':
        o.hide_render = True
# ground plane
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0.0))
g = bpy.context.object; mat = bpy.data.materials.new('ground'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.2, 0.15, 1); g.data.materials.append(mat)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.lens_unit = 'FOV'; cam.data.angle = math.radians(75); cam.data.clip_start = 0.002

def eye(pitch_deg):
    head = arm.matrix_world @ arm.pose.bones['Head'].head
    # On the brow, in front of the crest (measured head profile: brow top z 0.386 at y -0.31): the snout stays in the
    # lower part of the view.
    cam.location = (head.x, head.y - 0.034, head.z + 0.053)
    cam.rotation_euler = (math.radians(90 + pitch_deg), 0, math.radians(180))

def render(name):
    scene.frame_set(1)
    scene.render.filepath = f'{out}/{name}.png'
    bpy.ops.render.render(write_still=True)

eye(-12); render('eye_standing')

# Forelimbs into view: IK on each lower foreleg to a point ahead of the eye (right swipe mid-arc, left on guard).
def ik(side, target):
    e = bpy.data.objects.new(f'ik_{side}', None); scene.collection.objects.link(e); e.location = target
    c = arm.pose.bones[f'{side}ForeLower'].constraints.new('IK'); c.target = e; c.chain_count = 2
    return e
head = arm.matrix_world @ arm.pose.bones['Head'].head
ik('R', (head.x - 0.07, head.y - 0.11, head.z - 0.03))
ik('L', (head.x + 0.075, head.y - 0.07, head.z - 0.085))
eye(-12); render('eye_swipe')
# The same pose seen from the side: how the shoulder skin stretches.
cam.location = (0.55, -0.42, 0.33); cam.rotation_euler = (math.radians(88), 0, math.radians(95)); cam.data.angle = math.radians(40)
render('side_swipe')
# Close look at the right forefoot at about the distance a first-person claw sits from the eye.
foot = arm.matrix_world @ arm.pose.bones['RForeFoot'].head
cam.data.angle = math.radians(75)
cam.location = (foot.x - 0.01, foot.y + 0.09, foot.z + 0.05)
d = mathutils.Vector(foot) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
render('foot_close')
