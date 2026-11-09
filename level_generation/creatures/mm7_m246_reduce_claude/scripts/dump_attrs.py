"""Per-vertex master labels of the gate copy (work/gate_source.blend: same weld and vertex order as work/source.blend,
attributes 'garment', 'finger', 'piece' from the mm7_m246_claude master via gate_attrs.py) -> work/vattrs.npz."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'gate_source.blend'))
me = bpy.data.objects['Body'].data; out = {}
for n in ('garment', 'finger', 'piece'):
    a = np.zeros(len(me.vertices), np.int32); me.attributes[n].data.foreach_get('value', a); out[n] = a
out['co'] = np.array([v.co[:] for v in me.vertices])
np.savez(os.path.join(HERE, 'work', 'vattrs.npz'), **out)
print('VATTRS', {n: np.unique(a, return_counts=True)[0].tolist() for n, a in out.items() if n != 'co'})
