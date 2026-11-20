"""Render a sword GLB lying flat (ground item pose): an orthographic top view and an oblique close-up of the guard
and lower blade, under one sun plus a sky gradient (Eevee), for before/after comparisons.
Usage: blender --background --python render_sword.py -- <in.glb> <out_prefix> [size]
Writes <out_prefix>_top.png and <out_prefix>_close.png."""
import bpy, sys, math
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[0], args[1]
size = int(args[2]) if len(args) > 2 else 900
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
co = np.concatenate([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in meshes])
lo, hi = co.min(0), co.max(0)
ctr = (lo + hi) / 2
ext = hi - lo
long_axis = int(np.argmax(ext[:2]))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in
    bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('w')
scene.world = world
world.use_nodes = True
nt = world.node_tree
bg = nt.nodes['Background']
grad = nt.nodes.new('ShaderNodeTexGradient')
coord = nt.nodes.new('ShaderNodeTexCoord')
sep = nt.nodes.new('ShaderNodeSeparateXYZ')
ramp = nt.nodes.new('ShaderNodeValToRGB')
nt.links.new(coord.outputs['Generated'], sep.inputs[0])
nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
ramp.color_ramp.elements[0].color = (0.25, 0.22, 0.18, 1)
ramp.color_ramp.elements[1].color = (0.55, 0.65, 0.85, 1)
nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 1.0
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(30))
scene.collection.objects.link(sun)
scene.render.film_transparent = False


def shoot(name, loc, look, ortho=None, res=(size, size)):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    scene.collection.objects.link(cam)
    cam.location = Vector(loc)
    d = Vector(look) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho
    else:
        cam.data.lens = 50
    cam.data.clip_end = 10000
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = f'{out}_{name}.png'
    bpy.ops.render.render(write_still=True)


L = float(ext[long_axis])
up = [0, 0, 0]
top = [ctr[0], ctr[1], hi[2] + L]
shoot('top', top, ctr, ortho=L * 1.05, res=(size, size))
# Oblique close-up: look at the guard end (the widest slice region) from a low angle.
axis = np.zeros(3); axis[long_axis] = 1
proj = co[:, long_axis]
bins = np.linspace(lo[long_axis], hi[long_axis], 41)
widths = []
other = 1 - long_axis
for a, b in zip(bins[:-1], bins[1:]):
    sel = (proj >= a) & (proj < b)
    widths.append(np.ptp(co[sel, other]) if sel.sum() > 2 else 0)
gi = int(np.argmax(widths))
gpos = (bins[gi] + bins[gi + 1]) / 2
blade_dir = 1 if gpos < ctr[long_axis] else -1
focus = ctr.copy(); focus[long_axis] = gpos + blade_dir * 0.18 * L
cam = focus.copy(); cam[long_axis] -= blade_dir * 0.30 * L; cam[other] += 0.25 * L; cam[2] += 0.22 * L
shoot('close', cam, focus, res=(size, size))
