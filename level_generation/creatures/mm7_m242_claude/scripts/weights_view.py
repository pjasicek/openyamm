"""Dominant-bone colours of 'Body' (rest pose), front / left / back / three-quarter workbench renders.
Args: -- <blend> <out prefix> [z centre] [height]"""
import bpy, sys, os, colorsys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
zc = float(a[2]) if len(a) > 2 else 0.95; hh = float(a[3]) if len(a) > 3 else 2.0
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
b = bpy.data.objects['Body']; me = b.data
names = [g.name for g in b.vertex_groups]
col = me.color_attributes.new('dom', 'FLOAT_COLOR', 'POINT')
for v in me.vertices:
    if not v.groups:
        col.data[v.index].color = (0, 0, 0, 1); continue
    g = max(v.groups, key=lambda e: e.weight)
    h = (hash(names[g.group]) % 997) / 997.0
    r, gg, bb = colorsys.hsv_to_rgb(h, 0.75, 0.95); col.data[v.index].color = (r, gg, bb, 1)
me.color_attributes.active_color = col
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'VERTEX'
common.render_views(a[1], zc, hh, views=('front', 'left', 'back', 'three_quarter'), resolution=(700, 800))
