"""Front/left orthographic overlay: Body (red, wings hidden by z-clip) and Figure (cyan, translucent).
Usage (Blender): render_overlay.py <shell_fit.blend> <out_prefix>"""
import bpy, sys, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0]); sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH':
        o.hide_render = o.name not in ('Body', 'Figure')
def mat(name, rgb, alpha):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Alpha'].default_value = alpha
    m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    return m
for name, rgb, al in (('Body', (0.9, 0.2, 0.2), 1.0), ('Figure', (0.2, 0.8, 0.9), 0.45)):
    o = bpy.data.objects[name]; o.data.materials.clear(); o.data.materials.append(mat(name, rgb, al))
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 600; sc.render.resolution_y = 800
sun = bpy.data.objects.new('s', bpy.data.lights.new('s', 'SUN')); sc.collection.objects.link(sun)
sun.rotation_euler = (0.8, 0, 0.4)
cam = bpy.data.objects.new('c', bpy.data.cameras.new('c')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.9
c = Vector((0, 0, 0.8))
for v, d in (('front', (0, -1, 0)), ('left', (1, 0, 0))):
    cam.location = c + Vector(d) * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{args[1]}_{v}.png'; bpy.ops.render.render(write_still=True)
