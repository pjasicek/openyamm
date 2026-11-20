"""Bark UV orientation on the lower trunk of a built tree (work/<id>/tree.blend, LOD0): per bark face between 5 % and
30 % of the height, |du/dz| and |dv/dz| (texture repeats per metre of height) by least squares over its corners, and
the u span of one ring. Correct mapping: v follows the trunk (|dv/dz| ~ 1 / tile), u goes around (|du/dz| small).
Usage: blender --background --python check_bark_uv.py -- <tree.blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
o = bpy.data.objects['Tree']; me = o.data
bark = [i for i, m in enumerate(me.materials) if m.name == 'Bark'][0]
uv = me.uv_layers.active.data
H = max(v.co.z for v in me.vertices)
du, dv = [], []
for p in me.polygons:
    if p.material_index != bark or not (0.05 * H < p.center.z < 0.3 * H):
        continue
    zs = np.array([me.vertices[me.loops[l].vertex_index].co.z for l in p.loop_indices])
    if np.ptp(zs) < 0.02:
        continue
    us = np.array([uv[l].uv[0] for l in p.loop_indices]); vs = np.array([uv[l].uv[1] for l in p.loop_indices])
    du.append(abs(np.polyfit(zs, us, 1)[0])); dv.append(abs(np.polyfit(zs, vs, 1)[0]))
print('BARKUV faces', len(du), 'median |du/dz|', round(float(np.median(du)), 3), 'median |dv/dz|',
      round(float(np.median(dv)), 3))
