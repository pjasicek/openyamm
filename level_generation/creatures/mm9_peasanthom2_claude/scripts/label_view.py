"""Clay views of a master blend with face attributes coloured (head red, hand blue). Args: <blend> <out prefix>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
rig = body.parent
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
cols = []
for nm, c in (('base', (0.7, 0.7, 0.7, 1)), ('head', (0.9, 0.2, 0.2, 1)), ('hand', (0.2, 0.3, 0.9, 1))):
    m = bpy.data.materials.new(nm); m.diffuse_color = c; cols.append(m)
me.materials.clear()
for m in cols:
    me.materials.append(m)
hd = me.attributes.get('head'); hn = me.attributes.get('hand')
for p in me.polygons:
    p.material_index = 2 if (hn and hn.data[p.index].value) else (1 if (hd and hd.data[p.index].value) else 0)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH' and o is not body:
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = 700
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[2]) if len(a) > 2 else 2.0
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in a[3].split(',')]) if len(a) > 3 else Vector((0, 0, 0.05))
for v, d in {'front': Vector((0, -1, 0.05)), 'side': Vector((1, 0, 0.05)), 'back': Vector((0, 1, 0.05))}.items():
    cam.location = c + d.normalized() * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{v}.png'
    bpy.ops.render.render(write_still=True)
