"""Low vertices of 'Body' (z < Z): clusters by side and front/back with extents. Args: <blend> [Z]"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
Z = float(argv[1]) if len(argv) > 1 else 0.006
me = bpy.data.objects['Body'].data
part = np.array([d.value for d in me.attributes['part'].data])
P = np.array([tuple(v.co) for v in me.vertices])
low = P[(P[:, 2] < Z) & (part == 0)]
print('PAW all low', len(low), 'y %.4f..%.4f' % (low[:, 1].min(), low[:, 1].max()))
for sx in (1, -1):
    s = low[np.sign(low[:, 0]) == sx]
    ys = np.sort(s[:, 1])
    gap = np.argmax(np.diff(ys))
    cut = (ys[gap] + ys[gap + 1]) / 2
    for name, m in (('front', s[:, 1] < cut), ('hind', s[:, 1] >= cut)):
        c = s[m]
        print('PAW', sx, name, len(c), 'x %.4f..%.4f y %.4f..%.4f z %.4f..%.4f' % (c[:, 0].min(), c[:, 0].max(), c[:, 1].min(), c[:, 1].max(), c[:, 2].min(), c[:, 2].max()))
for y in np.arange(-0.08, 0.03, 0.005):
    sl = P[(np.abs(P[:, 1] - y) < 0.0025) & (part == 0)]
    if len(sl):
        print('SLICE y %.3f x %.4f..%.4f z %.4f..%.4f' % (y, sl[:, 0].min(), sl[:, 0].max(), sl[:, 2].min(), sl[:, 2].max()))
for y in np.arange(-0.085, 0.025, 0.005):
    sl = P[(np.abs(P[:, 1] - y) < 0.0025) & (part == 0)]
    c = sl[np.abs(sl[:, 0]) < 0.005]
    o = sl[np.abs(sl[:, 0]) >= 0.008]
    if len(c) and len(o):
        lo = o[o[:, 2] < 0.008]
        print('BELLY y %.3f centre zmin %.4f | outer low n %d x %.4f..%.4f' % (y, c[:, 2].min(), len(lo), np.abs(lo[:, 0]).min() if len(lo) else 0, np.abs(lo[:, 0]).max() if len(lo) else 0))
