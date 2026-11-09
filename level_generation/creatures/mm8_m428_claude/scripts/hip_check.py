"""Textured rest-pose views of the hips (back, both sides, front) from the textured master, and the open boundary
edges of piece 0 near the hips (holes). Args: -- <blend> <out prefix>"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); body = bpy.data.objects['Body']
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body: o.hide_render = True
bm = bmesh.new(); bm.from_mesh(body.data); pl = bm.verts.layers.int['piece']
hip = [e for e in bm.edges if e.is_boundary and all(v[pl] == 0 for v in e.verts)
       and all(0.85 < v.co.z < 1.15 and abs(v.co.x) > 0.12 for v in e.verts)]
print('HIPHOLES open piece-0 boundary edges at hip height, |x|>0.12:', len(hip),
      sorted({(round(e.verts[0].co.x, 2), round(e.verts[0].co.y, 2), round(e.verts[0].co.z, 2)) for e in hip})[:12])
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = False
sh.background_type = 'VIEWPORT'; sh.background_color = (0.3, 0.32, 0.35); sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.7
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, 0, 1.0))
for view, d in (('back', Vector((0, 1, 0))), ('right', Vector((-1, 0, 0))), ('left', Vector((1, 0, 0))), ('front', Vector((0, -1, 0)))):
    cam.location = c + d * 3; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{view}.png'; bpy.ops.render.render(write_still=True)
