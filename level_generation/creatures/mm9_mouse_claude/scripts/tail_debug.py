import bpy, sys, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects['Body'].data
P = np.array([tuple(v.co) for v in me.vertices]); t = np.array([d.value for d in me.attributes['tail_t'].data])
for k in [0, 0.02, 0.05, 0.1, 0.2, 0.4, 0.7, 0.95]:
    s = P[np.abs(t - k) < 0.006]
    if len(s): print('RING', k, len(s), 'x %.4f..%.4f y %.4f..%.4f z %.4f..%.4f' % (s[:,0].min(), s[:,0].max(), s[:,1].min(), s[:,1].max(), s[:,2].min(), s[:,2].max()))
