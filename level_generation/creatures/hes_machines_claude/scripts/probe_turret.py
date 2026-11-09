"""Print the turret's barrel/recoil geometry facts used by build_machine.py (axis, muzzle, pods). Args: -- <name>"""
import os
import sys

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import machines_common as mc  # noqa: E402

name = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{name}_tex.blend'))
me = bpy.data.objects[name].data
part = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', part)
bm = bmesh.new(); bm.from_mesh(me)
fpart = bm.faces.layers.int['part']
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
labels = mc.component_labels(bm)
vpart = np.zeros(len(bm.verts), int)
for f in bm.faces:
    for v in f.verts:
        vpart[v.index] = f[fpart]
co = np.array([v.co[:] for v in bm.verts])
for c in range(labels.max() + 1):
    sel = labels == c
    p = co[sel]
    if len(p) < 8:
        continue
    pp = np.bincount(vpart[sel]).argmax()
    if pp in (3, 4):
        print('COMP part', pp, 'c', c, 'n', len(p), 'lo', p.min(0).round(3).tolist(), 'hi', p.max(0).round(3).tolist())
