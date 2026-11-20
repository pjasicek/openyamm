"""UV gate for work/step1_uv.blend: texel density (texels/cm at 2048) per uv_region with p10/p50/p90 over faces,
UV coverage, and work/uv_layout.json for draw_uv_layout.py. Density spread inside a region shows collapsed islands."""
import bpy, sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv
                                               else 'step1_uv.blend'))
me = bpy.data.objects['Thief'].data
names = json.loads(bpy.context.scene['thf_uv_regions'])
reg = np.zeros(len(me.polygons), int)
me.attributes['uv_region'].data.foreach_get('value', reg)
uvl = me.uv_layers.active.data
dens = {n: [] for n in names}
a3t = {n: 0.0 for n in names}
a2t = {n: 0.0 for n in names}
faces = []
for p in me.polygons:
    pts = [tuple(uvl[li].uv) for li in p.loop_indices]
    a2 = abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                 for i in range(len(pts)))) / 2
    n = names[reg[p.index]]
    a3t[n] += p.area
    a2t[n] += a2
    if p.area > 1e-9:
        dens[n].append(math.sqrt(a2 / p.area) * 2048 / 100)
    faces.append([int(reg[p.index]), pts])
rep = {}
for n in names:
    d = np.array(dens[n])
    rep[n] = {'mean': round(math.sqrt(a2t[n] / max(a3t[n], 1e-9)) * 2048 / 100, 2),
              'p10': round(float(np.percentile(d, 10)), 2), 'p50': round(float(np.percentile(d, 50)), 2),
              'p90': round(float(np.percentile(d, 90)), 2), 'uv_share': round(a2t[n], 4), 'faces': len(d)}
    print('UVREG', n, rep[n])
print('UV coverage', round(sum(a2t.values()), 3))
json.dump({'regions': names, 'faces': faces}, open(os.path.join(common.WORK, 'uv_layout.json'), 'w'))
json.dump(rep, open(os.path.join(common.WORK, 'uv_density.json'), 'w'), indent=1)
