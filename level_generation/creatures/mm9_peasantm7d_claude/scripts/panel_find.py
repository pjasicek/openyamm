"""Blender: locate the flat throat panel (PeasantM7's olive undershirt collar piece, inside the tunic's V): face-shell faces
below z 0.70 facing forward (normal y < -0.75, glTF -z), |x - mid| < 0.06; clay shot with them red, and their HeadUV
triangles dumped to work/panel_faces.npz. Args: <blend> <out png>"""
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; me = body.data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
MID = -0.0111
sel = []
for p in me.polygons:
    c = p.center; n = p.normal
    if hd[p.index] and not hn[p.index] and c.z < 0.70 and n.y < -0.75 and abs(c.x - MID) < 0.06 and c.y < -0.03:
        sel.append(p.index)
print('PANEL faces', len(sel), 'y range', min(me.polygons[i].center.y for i in sel), max(me.polygons[i].center.y for i in sel),
      'z range', min(me.polygons[i].center.z for i in sel), max(me.polygons[i].center.z for i in sel))
uv = me.uv_layers['HeadUV'].data
UV = []
for i in sel:
    l = list(me.polygons[i].loop_indices)
    for k in range(1, len(l) - 1):
        UV.append([uv[j].uv[:] for j in (l[0], l[k], l[k + 1])])
np.savez(os.path.join(os.path.dirname(a[1]), '..', 'work', 'panel_faces.npz'), UV=np.array(UV))
me.materials.clear()
for name, col in (('b', (0.55, 0.55, 0.58, 1)), ('h', (0.8, 0.7, 0.62, 1)), ('p', (0.9, 0.2, 0.15, 1))):
    m = bpy.data.materials.new(name); m.diffuse_color = col; me.materials.append(m)
mi = np.where(hd > 0, 1, 0); mi[sel] = 2
me.polygons.foreach_set('material_index', mi.tolist())
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = 500
w = bpy.data.worlds.new('w'); sc.world = w
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 0.35
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((MID, 0, 0.68)); d = Vector((0, -1, 0.1)).normalized(); cam.location = c + d * 3
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = a[1]; bpy.ops.render.render(write_still=True)
