"""Check that the reduced rig mesh still carries 'orig_co' consistent with reshape: |reshape(orig_co) - co| per vertex.
Args: -- <blend>"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reshape
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
me = bpy.data.objects['Body'].data
oc = np.zeros(len(me.vertices) * 3); me.attributes['orig_co'].data.foreach_get('vector', oc); oc = oc.reshape(-1, 3)
co = np.array([tuple(v.co) for v in me.vertices])
d = np.linalg.norm(reshape.arm_apply(reshape.apply(oc)) - co, axis=1) * 1000
print('ORIGCO verts', len(co), 'mismatch mm p50/p99/max', round(float(np.median(d)), 3), round(float(np.percentile(d, 99)), 3), round(float(d.max()), 3),
      'moved by reshape mm max', round(float(np.linalg.norm(co - oc, axis=1).max() * 1000), 1))
