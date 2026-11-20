"""Identical-camera stills for the texture quality pass before/after sheets (after ../mm9_magreeb_claude's
texpass_views.py): Eevee, one sun from above-front plus a grey sky, Standing frame 0, LOD0 only.

Args: -- <in.glb> <out prefix> <shots json>
The shots json lists {"name", "target": bone name or [x, y, z] or a list of bone names (their mean), "dir": [x, y, z]
(camera direction from the target), "dist": metres, "lens": mm}. Writes <prefix>_<name>.png (1000 x 700).
The creature faces -Y."""
import bpy, sys, json
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
glb, out, shots = args[0], args[1], json.load(open(args[2]))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if rig.animation_data and 'Standing' in bpy.data.actions:
    rig.animation_data.action = bpy.data.actions['Standing']
sc = bpy.context.scene
sc.frame_set(0)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = any(t in o.name for t in ('LOD', 'Shadow'))
bpy.context.view_layer.update()
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1000, 700
world = bpy.data.worlds.new('w')
sc.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.32, 0.33, 0.35, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.2
sc.collection.objects.link(sun)
sun.rotation_euler = Vector((0.2, -0.6, 1.0)).to_track_quat('Z', 'Y').to_euler()
sc.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
sc.collection.objects.link(cam)
sc.camera = cam


def point(t):
    if isinstance(t, str):
        return rig.matrix_world @ rig.pose.bones[t].head
    if isinstance(t[0], str):
        ps = [rig.matrix_world @ rig.pose.bones[n].head for n in t]
        return sum(ps, Vector()) / len(ps)
    return Vector(t)


for s in shots:
    target = point(s['target'])
    cam.data.lens = s.get('lens', 50)
    cam.location = target + Vector(s['dir']).normalized() * s['dist']
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"{out}_{s['name']}.png"
    bpy.ops.render.render(write_still=True)
print('VIEWS', out, len(shots))
