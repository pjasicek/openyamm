"""Clay ortho renders of the rest-pose head (front and right side, exact axes) with a 1 cm-per-tick frame for picking
eye positions: 600 px over 0.42 m centred at (0, -0.2, 1.66). Usage: blender -b -P head_probe.py -- <blend> <label>"""
import math, os, sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, a[0]))
sc = bpy.context.scene; body = bpy.data.objects['CrystalWalker']; rig = bpy.data.objects.get('CrystalRig')
if rig and rig.animation_data:
    rig.animation_data.action = None
if rig:
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
if os.environ.get('HP_ONLY'):   # 'body' or 'head': keep only those faces (part attribute)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(body.data); lay = bm.faces.layers.int.get('part')
    if lay is not None:
        keep_head = os.environ['HP_ONLY'] == 'head'
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if (f[lay] > 0) != keep_head], context='FACES')
    bm.to_mesh(body.data); bm.free()
mat = bpy.data.materials.new('clay'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.8, .7, .75, 1)
body.data.materials.clear(); body.data.materials.append(mat)
for o in list(bpy.data.objects):
    if o.type in ('LIGHT', 'CAMERA'):
        bpy.data.objects.remove(o)
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 600
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.2, .2, .22, 1)
s = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); s.data.energy = 3; sc.collection.objects.link(s); s.rotation_euler = (math.radians(60), 0, math.radians(20))
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = float(os.environ.get('HP_SCALE', .42)); c = Vector((0, -.2, 1.66))
for name, d in (('front', Vector((0, -1, 0))), ('side', Vector((1, 0, 0))), ('top', Vector((0, -.001, 1)))):
    cam.location = c + d * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(P, 'review', 'inspect', f'{a[1]}_{name}.png'); bpy.ops.render.render(write_still=True)
