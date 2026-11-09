"""Open the jaw by posing an MM9 action at a time (or rotating Xjawpivot) and render the head: weights colour
(upper blue / lower red / mouth faces palate pink, floor orange) and clay. Args: -- <blend> <out prefix> <angle deg>
[views]"""
import bpy, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]; 
views = a[3].split(',') if len(a) > 3 else ['side', 'q34', 'front', 'below']
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); body = bpy.data.objects.get('Body') or bpy.data.objects['DragonKing']; me = body.data
for o in bpy.data.objects:
    if o.type == 'MESH' and o != body: o.hide_render = True
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
import json, os
if '@' in a[2]:
    clip, t = a[2].split('@'); t = float(t)
    rig.animation_data_create(); rig.animation_data.action = bpy.data.actions[clip]
    sc0 = bpy.context.scene; sc0.render.fps = 30; f = t * 30
    sc0.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
bpy.context.view_layer.update()
UPPER = {'Xheadpiv', 'Xhead', 'Xjawbase', 'Xtopfinpiv', 'Xtopfinpiv01', 'Xfinpiv', 'Xfinpiv01'}
LOWER = {'Xjaw', 'Xjawpivot', 'Xchinfinpiv', 'Xchinfinpiv01', 'Xbotfinpiv', 'Xbotfinpiv01', 'Xtong', 'Xtongpiv'}
vg = {g.index: g.name for g in body.vertex_groups}
ca = me.color_attributes.new('jw', 'BYTE_COLOR', 'CORNER')
mouth = me.attributes.get('mouth')
for p in me.polygons:
    mo = mouth.data[p.index].value if mouth else 0
    for li, vi in zip(p.loop_indices, p.vertices):
        v = me.vertices[vi]; s = sum(g.weight for g in v.groups) or 1
        u = sum(g.weight for g in v.groups if vg[g.group] in UPPER) / s; l = sum(g.weight for g in v.groups if vg[g.group] in LOWER) / s
        if mo == 1: c = (0.95, 0.55 + 0.3 * u, 0.7, 1)
        elif mo == 2: c = (0.95, 0.6, 0.15 + 0.4 * u, 1)
        else: c = (0.3 + 0.6 * l, 0.35, 0.3 + 0.6 * u, 1)
        ca.data[li].color = c
me.color_attributes.active_color = ca
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'VERTEX'; sc.render.resolution_x = sc.render.resolution_y = 700
sc.display.shading.show_backface_culling = False
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.85, 0.85, 0.88)
MW = rig.matrix_world
hp_ = MW @ rig.pose.bones['Xheadpiv'].head; sn_ = MW @ rig.pose.bones['Xjaw'].head
hc = hp_ * 0.35 + sn_ * 0.65
fwd = (sn_ - hp_); fwd.z = 0; fwd.normalize(); lft = Vector((0, 0, 1)).cross(fwd).normalized()
def vdir(d):
    return (lft * -d[0] + fwd * -d[1] + Vector((0, 0, 1)) * d[2])
cd = bpy.data.cameras.new('c'); cd.lens = 85; cd.clip_start = 0.01; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
V = {'side': (1, -0.15, 0.05), 'sideL': (-1, -0.15, 0.05), 'q34': (0.6, -1, 0.15), 'front': (0.05, -1, 0.1), 'below': (0.15, -0.4, -1),
     'q34low': (0.5, -1, -0.35)}
for nm in views:
    cam.location = hc + vdir(Vector(V[nm])).normalized() * 9.0
    cam.rotation_euler = (hc - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{nm}.png'; bpy.ops.render.render(write_still=True)
