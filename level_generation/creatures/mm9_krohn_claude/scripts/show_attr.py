"""Render Body with faces of an INT face attribute highlighted (red = 1). Args: blend attr outprefix size ortho cx,cy,cz views"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
vals = [0] * len(me.polygons); me.attributes[a[1]].data.foreach_get('value', vals)
me.materials.clear()
for name, col in (('n', (0.7, 0.7, 0.7, 1)), ('y', (0.9, 0.2, 0.2, 1))):
    m = bpy.data.materials.new(name); m.diffuse_color = col; me.materials.append(m)
for p in me.polygons:
    p.material_index = 1 if vals[p.index] else 0
for o in bpy.data.objects:
    if o.type == 'MESH' and o != body:
        o.hide_render = True
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = int(a[3])
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.3, 0.3, 0.3); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[4]); cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in a[5].split(',')])
dirs = {'front': Vector((0, -1, 0.05)), 'q34': Vector((-1, -1.25, 0.4)), 'left': Vector((1, 0, 0.05)), 'back': Vector((0, 1, 0.05))}
for v in a[6].split(','):
    d = dirs[v].normalized(); cam.location = c + d * 20; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[2]}_{v}.png'; bpy.ops.render.render(write_still=True)
