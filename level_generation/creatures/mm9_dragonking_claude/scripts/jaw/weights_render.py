"""Vertex colours by jaw side (upper blue, lower red, mix purple; neck grey) on a blend's Body, bind pose, workbench.
Args: -- <blend> <out prefix>"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
body = bpy.data.objects['Body']; me = body.data
for o in bpy.data.objects:
    if o.type == 'MESH' and o != body: o.hide_render = True
UPPER = {'Xheadpiv', 'Xhead', 'Xjawbase', 'Xtopfinpiv', 'Xtopfinpiv01', 'Xfinpiv', 'Xfinpiv01'}
LOWER = {'Xjaw', 'Xjawpivot', 'Xchinfinpiv', 'Xchinfinpiv01', 'Xbotfinpiv', 'Xbotfinpiv01', 'Xtong', 'Xtongpiv'}
vg = {g.index: g.name for g in body.vertex_groups}
ca = me.color_attributes.new('jw', 'FLOAT_COLOR', 'POINT')
for v in me.vertices:
    s = sum(g.weight for g in v.groups) or 1
    u = sum(g.weight for g in v.groups if vg[g.group] in UPPER) / s
    l = sum(g.weight for g in v.groups if vg[g.group] in LOWER) / s
    fin = sum(g.weight for g in v.groups if 'fin' in vg[g.group]) / s
    r = 0.25 + 0.75 * l; b = 0.25 + 0.75 * u; g_ = 0.25 + 0.5 * fin
    ca.data[v.index].color = (r, g_, b, 1)
me.color_attributes.active_color = ca
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'VERTEX'; sc.render.resolution_x = sc.render.resolution_y = 700
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.9, 0.9, 0.92)
hc = Vector((0, -3.6, 15.4))
cd = bpy.data.cameras.new('c'); cd.lens = 85; cd.clip_start = 0.01; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for nm, d in (('sideR', (1, -0.1, 0.1)), ('sideL', (-1, -0.1, 0.1)), ('frontlow', (0.3, -1, -0.35))):
    cam.location = hc + Vector(d).normalized() * 8
    cam.rotation_euler = (hc - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{nm}.png'; bpy.ops.render.render(write_still=True)
