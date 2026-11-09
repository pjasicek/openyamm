"""Render 'Body' with loose parts below N vertices in red (diagnosis). Args: <blend> <out png> <maxverts> <cx,cy,cz> <ortho> [view]"""
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data
rig = ob.parent
if rig:
    for pb in rig.pose.bones: pb.matrix_basis.identity()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); col = [0] * len(me.vertices)
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; comp = []; seen.add(v.index)
    while st:
        x = st.pop(); comp.append(x.index)
        for e in x.link_edges:
            o = e.other_vert(x)
            if o.index not in seen: seen.add(o.index); st.append(o)
    if len(comp) <= int(a[2]):
        for i in comp: col[i] = 1
import os
FA = os.environ.get('FACE_ATTR')
if FA:
    attr = me.color_attributes.new('pc', 'FLOAT_COLOR', 'CORNER')
    fa = me.attributes[FA].data
    for p in me.polygons:
        for l in p.loop_indices:
            attr.data[l].color = (1, 0.1, 0.1, 1) if fa[p.index].value else (0.7, 0.7, 0.7, 1)
else:
    attr = me.color_attributes.new('pc', 'FLOAT_COLOR', 'POINT')
    for i, c in enumerate(col):
        attr.data[i].color = (1, 0.1, 0.1, 1) if c else (0.7, 0.7, 0.7, 1)
me.color_attributes.active_color = attr
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'VERTEX'
sc.render.resolution_x = sc.render.resolution_y = 900
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[4])
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in a[3].split(',')])
d = {'front': Vector((0, -1, 0.05)), 'q34': Vector((-0.8, -1, 0.2)), 'left': Vector((1, 0, 0.05)), 'right': Vector((-1, 0, 0.05)), 'top': Vector((0, -0.01, 1)), 'below': Vector((0, -0.01, -1)), 'back': Vector((0, 1, 0.05))}[a[5] if len(a) > 5 else 'front'].normalized()
cam.location = c + d * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = a[1]; bpy.ops.render.render(write_still=True)
