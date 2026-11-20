"""Render one object of a .blend by a colour attribute (flat emission), from front/back/left/quarter.
Usage (Blender): render_attr.py <in.blend> <object> <attribute> <out_prefix> [size] [also_show_object]"""
import bpy, sys, math
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
src, obname, attr, out = args[:4]
size = int(args[4]) if len(args) > 4 else 600
also = args[5] if len(args) > 5 else None
bpy.ops.wm.open_mainfile(filepath=src)
sc = bpy.context.scene
ob = bpy.data.objects[obname]
for o in sc.objects:
    if o.type == 'MESH':
        o.hide_render = o.name not in (obname, also)
m = bpy.data.materials.new('attr'); m.use_nodes = True
nt = m.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
outn = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = attr
dif = nt.nodes.new('ShaderNodeBsdfDiffuse'); mix = nt.nodes.new('ShaderNodeAddShader')
nt.links.new(at.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 0.6
nt.links.new(at.outputs['Color'], dif.inputs['Color'])
nt.links.new(em.outputs[0], mix.inputs[0]); nt.links.new(dif.outputs[0], mix.inputs[1])
nt.links.new(mix.outputs[0], outn.inputs['Surface'])
ob.data.materials.clear(); ob.data.materials.append(m)
co = np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices])
lo, hi = co.min(0), co.max(0); c = Vector((lo + hi) / 2); ext = float(np.linalg.norm(hi - lo))
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True
sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.3, 0.3, 0.32, 1)
sc.render.resolution_x = size; sc.render.resolution_y = int(size * 1.4)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 2.5
sc.collection.objects.link(sun); sun.rotation_euler = (math.radians(45), 0, math.radians(-30))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(hi[2] - lo[2]) * 1.1
for view, d in {'front': (0, -1, 0), 'back': (0, 1, 0), 'left': (1, 0, 0), 'quarter': (0.6, -0.8, 0.1)}.items():
    d = Vector(d).normalized(); cam.location = c + d * ext * 2
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{view}.png'; bpy.ops.render.render(write_still=True)
