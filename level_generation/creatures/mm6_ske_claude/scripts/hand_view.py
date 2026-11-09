"""Right-hand close-ups of a rig blend as saved (current pose), with the posed mesh applied and everything farther
than 0.2 m from the hand removed (the left hand lines up behind it in side views). Args: -- <blend> <tag>"""
import bpy, bmesh, sys, os
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
body = bpy.data.objects['Skeleton']
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.convert(target='MESH')
centre = Vector((-0.43, -0.01, 0.80))
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if (body.matrix_world @ v.co - centre).length > 0.2], context='VERTS')
bm.to_mesh(body.data); bm.free()
scene = bpy.context.scene; common.workbench_clay(scene)
scene.display.shading.color_type = 'MATERIAL'
out = os.path.join(common.REVIEW, tag)
for v in ('front', 'left', 'right', 'back', 'three_quarter'):
    common.render_views(out + '_hand', 0.80, 0.24, views=(v,), resolution=(450, 450), target=(-0.43, -0.01))
