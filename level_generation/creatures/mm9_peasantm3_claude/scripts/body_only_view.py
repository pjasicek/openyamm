"""Diagnostic: render the master with the head-set (and hand) faces deleted, front and 3/4, around the neck base: does the
body set close the throat under the head apron? Args (Blender): <blend> <out png>"""
import bpy, bmesh, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me)
lh = bm.faces.layers.int['head']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lh]], context='FACES')
bm.to_mesh(me); bm.free()
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body:
        o.hide_render = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.display.shading.show_backface_culling = True
sc.render.resolution_x = 900; sc.render.resolution_y = 450
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.9, 0.2, 0.9)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.36
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, -0.04, 0.63))
cam.location = c + Vector((0, -1, 0.15)).normalized() * 2
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = a[1]; bpy.ops.render.render(write_still=True)
