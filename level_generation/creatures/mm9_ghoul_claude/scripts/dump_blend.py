import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
out = {}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    me = o.data
    me.calc_loop_triangles()
    out[o.name + '_V'] = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])
    out[o.name + '_F'] = np.array([t.vertices[:] for t in me.loop_triangles])
    if 'part' in me.attributes:
        pa = np.zeros(len(me.vertices), int); me.attributes['part'].data.foreach_get('value', pa); out[o.name + '_part'] = pa
np.savez(a[1], **out)
