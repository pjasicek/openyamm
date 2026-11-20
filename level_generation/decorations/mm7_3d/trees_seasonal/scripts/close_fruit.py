"""Close review render of a food tree's LOD0 (review/<id>/fruit_close.png): camera 1.7 x the tree height out at crown height, Eevee,
sun + sky, base colour x COLOR_0 as render_review.py. Usage: blender --background --python close_fruit.py -- <id>"""
import bpy, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
spec = common.load()
bpy.ops.wm.open_mainfile(filepath=os.path.join(spec['work'], 'tree_export.blend'))
sc = bpy.context.scene
for o in bpy.data.objects:
    o.hide_render = o.name != 'Tree'
sc.render.engine = 'BLENDER_EEVEE'; sc.render.film_transparent = True
sc.render.resolution_x = sc.render.resolution_y = 600; sc.view_settings.view_transform = 'Standard'
w = sc.world or bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.5
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None or not bsdf.inputs['Base Color'].links:
        continue
    tex = bsdf.inputs['Base Color'].links[0].from_node
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Color'
    mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
    nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
    nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.6; sun.data.color = (1.0, 0.95, 0.86); sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
H = spec['height_m']; cam.data.lens = 70; cam.location = (0, -1.7 * H, 0.55 * H)
cam.rotation_euler = (Vector((0, 0, 0.55 * H)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = os.path.join(spec['review'], 'fruit_close.png'); bpy.ops.render.render(write_still=True)
print('CLOSE', sc.render.filepath)
