"""Clay preview of work/staff.npz (backfaces red): head front, quarter, from above. Args: <out png prefix>"""
import bpy, sys, mathutils
import numpy as np
out = sys.argv[sys.argv.index('--') + 1]
d = np.load(bpy.path.abspath('//') + 'work/staff.npz') if False else np.load(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))), 'work', 'staff.npz'))
V, F = d['V'], d['F']
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('s'); me.from_pydata([(v[0], v[2], v[1]) for v in V], [], F[:, ::-1].tolist()); me.update()
o = bpy.data.objects.new('s', me); bpy.context.scene.collection.objects.link(o)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.show_backface_culling = True
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.8, 0.1, 0.1)
sc.render.resolution_x = sc.render.resolution_y = 700
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 0.55; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
c = mathutils.Vector((0, 0, 1.08))
for k, dd in enumerate([(0, -1, 0.15), (1, -1, 0.5), (0, -0.3, 1)]):
    v = mathutils.Vector(dd).normalized(); cam.location = c + v * 5; cam.rotation_euler = (-v).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{k}.png'; bpy.ops.render.render(write_still=True)
