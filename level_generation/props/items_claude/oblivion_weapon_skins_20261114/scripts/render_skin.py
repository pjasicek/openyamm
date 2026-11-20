"""Lit review renders of a weapon GLB (template or skin): the whole weapon from a three-quarter view and a close-up of
its working end (guard and lower blade, mace head, bow riser), Eevee under a sun and a sky-to-ground gradient.
Usage: blender --background --python render_skin.py -- <template> <in.glb> <out_prefix> [size]
Writes <out_prefix>_full.png and <out_prefix>_close.png."""
import bpy, sys, math
import numpy as np
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index('--') + 1:]
NAME, GLB, OUT = args[0], args[1], args[2]
SIZE = int(args[3]) if len(args) > 3 else 900
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and (NAME != 'w_bow' or o.data.name.startswith('Bow'))]
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in meshes:
        o.hide_render = True
for o in meshes:
    for m in o.data.materials:
        m.use_backface_culling = False
co = np.concatenate([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in meshes])
lo, hi = co.min(0), co.max(0)
ctr = (lo + hi) / 2
L = float(np.ptp(co[:, 2]))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in
    bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
nt = world.node_tree
bg = nt.nodes['Background']
coord = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
ramp = nt.nodes.new('ShaderNodeValToRGB')
nt.links.new(coord.outputs['Generated'], sep.inputs[0])
nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
ramp.color_ramp.elements[0].position = 0.45
ramp.color_ramp.elements[0].color = (0.18, 0.16, 0.13, 1)
ramp.color_ramp.elements[1].position = 0.6
ramp.color_ramp.elements[1].color = (0.75, 0.8, 0.9, 1)
nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 0.8
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(55), math.radians(10), math.radians(-35))
scene.collection.objects.link(sun)
scene.render.film_transparent = False


def shoot(name, loc, look, lens):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    scene.collection.objects.link(cam)
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(look) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 10000
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = SIZE * 2 // 3, SIZE
    scene.render.filepath = f'{OUT}_{name}.png'
    bpy.ops.render.render(write_still=True)


# Three-quarter view of the whole weapon (its flat toward -Y, turned 35 degrees).
d = Vector((math.sin(math.radians(35)), -math.cos(math.radians(35)), 0.15)).normalized()
shoot('full', Vector(ctr.tolist()) + d * L * 2.2, ctr.tolist(), 50)
# Close-up of the working end: swords the guard and lower blade, the mace its head, the bow its riser.
focus = ctr.copy()
if NAME in ('w_longsword', 'w_claymore'):
    focus[2] = lo[2] + 0.38 * L
elif NAME == 'w_mace':
    focus[2] = hi[2] - 0.2 * L
d2 = Vector((math.sin(math.radians(30)), -math.cos(math.radians(30)), 0.25)).normalized()
shoot('close', Vector(focus.tolist()) + d2 * L * 0.75, focus.tolist(), 50)
