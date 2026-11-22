"""Dominant-bone colour views of work/rig_v1.blend (review/weights_<view>.png)."""
import bpy, os, sys, colorsys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
m = bpy.data.objects['Dillo']; me = m.data
names = [g.name for g in m.vertex_groups]
pal = {}
for k, n in enumerate(sorted(names)):
    pal[n] = colorsys.hsv_to_rgb((k * 0.61803) % 1, 0.75, 0.95)
ca = me.color_attributes.new('dom', 'FLOAT_COLOR', 'POINT')
for v in me.vertices:
    g = max(v.groups, key=lambda g: g.weight)
    ca.data[v.index].color = (*pal[names[g.group]], 1)
me.color_attributes.active_color = ca
for view, (loc, tgt) in {'top': ((0, 0, 3), (0, 0, 0)), 'front': ((0, -3, 0.25), (0, 0, 0.25)),
                         'side': ((3, 0, 0.25), (0, 0, 0.25)),
                         'quarter': ((1.8, -2.2, 1.4), (0.1, -0.2, 0.25)), 'under': ((0, 0, -3), (0, 0, 0.2))}.items():
    C.render(loc, tgt, 2.4, os.path.join(HERE, 'review', f'weights_{view}.png'), res=(800, 700), floor=False, color='VERTEX')
