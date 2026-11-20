# Blender: a first-person "view model" made from the installed MM8 Dragon's forelimbs (mm8_m492), the way the
# Oblivion arms are a separate first-person skeleton: only the vertices of the two forelegs are kept, the legs are
# raised by IK into poses in front of an eye placed between the shoulders, and the frames are rendered with a
# transparent film at 1600x900 (60 degree vertical field of view, as FirstPersonViewModel) for compositing.
# blender -b --python render_viewmodel.py -- <mm8_m492.glb> <out_dir>
import bpy, sys, math
args = sys.argv[sys.argv.index('--') + 1:]
src, out = args[0], args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.render.film_transparent = True
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.62, 0.70, 0.82, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(40), math.radians(-25), math.radians(150))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.animation_data.action = None
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body':
        o.hide_render = True
body = bpy.data.objects['Body']
# Keep only the forelegs: vertices whose foreleg weights sum over half.
fore = {g.index for g in body.vertex_groups if 'Fore' in g.name}
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for v in body.data.vertices:
    w = sum(g.weight for g in v.groups if g.group in fore)
    v.select = w < 0.5
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='VERT'); bpy.ops.object.mode_set(mode='OBJECT')
print('kept vertices', len(body.data.vertices))

targets = {}
for side in ('L', 'R'):
    e = bpy.data.objects.new(f'ik_{side}', None); scene.collection.objects.link(e); targets[side] = e
    c = arm.pose.bones[f'{side}ForeLower'].constraints.new('IK'); c.target = e; c.chain_count = 2
    # The foot keeps a world rotation per pose (talons forward, palm down or turned in a swipe).
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(60); cam.data.clip_start = 0.002
# Eye between and above the shoulders (shoulders at x +-0.043, y -0.25, z 0.185; the model faces -Y).
cam.location = (0.0, -0.215, 0.275)
cam.rotation_euler = (math.radians(90 - 14), 0, math.radians(180))

POSES = {
    # name: (right target, left target); world -X is screen right.
    'guard': ((-0.07, -0.385, 0.235), (0.07, -0.385, 0.235)),
    'swipe_wind': ((-0.10, -0.34, 0.30), (0.065, -0.38, 0.215)),
    'swipe_hit': ((0.015, -0.405, 0.27), (0.07, -0.37, 0.205)),
    'swipe_left_hit': ((-0.065, -0.37, 0.205), (-0.015, -0.405, 0.27)),
}
for name, (r, l) in POSES.items():
    targets['R'].location = r; targets['L'].location = l
    bpy.context.view_layer.update()
    scene.frame_set(1)
    scene.render.filepath = f'{out}/vm_{name}.png'
    bpy.ops.render.render(write_still=True)
