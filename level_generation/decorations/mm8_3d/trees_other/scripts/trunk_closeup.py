"""Close render of the lower trunk (bark texture orientation check): Eevee, sun + sky, base colour x COLOR_0, camera
at 15 % of the height looking at the trunk foot from 3 trunk diameters. Usage: blender --background --python
trunk_closeup.py -- <tree.blend> <out.png>"""
import bpy, sys, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
sc = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        continue
sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = True
sc.render.resolution_x = 600; sc.render.resolution_y = 600
world = sc.world or bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs['Strength'].default_value = 0.5
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.6; sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
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
tree = bpy.data.objects['Tree']
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o is not tree
me = tree.data
bark = [i for i, m in enumerate(me.materials) if m.name == 'Bark'][0]
H = max(v.co.z for v in me.vertices)
ring = [v.co for p in me.polygons if p.material_index == bark for v in (me.vertices[i] for i in p.vertices)
        if 0.12 * H < v.co.z < 0.18 * H]
c = sum(ring, Vector()) / len(ring)
r = max((Vector((q.x - c.x, q.y - c.y)).length for q in ring))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
cam.location = Vector((c.x, c.y - 7 * r, c.z + 0.5 * r))
cam.rotation_euler = (Vector((c.x, c.y, c.z)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = args[1]; bpy.ops.render.render(write_still=True)
