"""Rest positions, part ids and face lists of the master for the skirt gate. Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
n = len(me.vertices)
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
pid = np.zeros(n, np.int32); me.attributes['pid'].data.foreach_get('value', pid)
f = np.array([p.vertices[:] for p in me.polygons])
fn = len(f); lin = np.zeros(fn, np.int32); me.attributes['lining'].data.foreach_get('value', lin)
rig = b.parent
J = {x.name: np.array(rig.matrix_world @ x.head_local) for x in rig.data.bones}
np.savez(a[1], co=co, pid=pid, f=f, lining=lin, jn=np.array(list(J)), jp=np.array(list(J.values())))
print('DUMP', n, fn, sorted(set(pid.tolist()))[:60])
