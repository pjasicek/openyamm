"""Textured EEVEE close-up of the head (front, three-quarter) of a rig blend at rest. Args: -- <blend> <out prefix>"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 500
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[1].default_value = 1.4
sun = bpy.data.objects.new('s', bpy.data.lights.new('s', 'SUN')); sc.collection.objects.link(sun); sun.rotation_euler = (0.9, 0.2, -0.4)
c = Vector((0, -0.08, 1.64))
for name, d in (('front', (0, -1, 0.05)), ('tq', (-0.6, -0.8, 0.1))):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(cam); cam.data.lens = 60
    cam.location = c + Vector(d).normalized() * 0.9; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam; sc.render.filepath = f'{a[1]}_{name}.png'; bpy.ops.render.render(write_still=True)
print('HEADSHOT', a[1])
