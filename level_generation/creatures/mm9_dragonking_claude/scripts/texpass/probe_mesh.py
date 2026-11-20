"""Face sizes and head/mouth tags of the master mesh. Args: <blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
b = bpy.data.objects['Body']; me = b.data
n = np.array([len(p.vertices) for p in me.polygons])
hd = np.zeros(len(n), np.int32); me.attributes['head'].data.foreach_get('value', hd)
mo = np.zeros(len(n), np.int32); me.attributes['mouth'].data.foreach_get('value', mo)
print('PROBE sizes', np.unique(n, return_counts=True), 'nonhead', np.unique(n[hd == 0], return_counts=True),
      'head nonmouth', np.unique(n[(hd > 0) & (mo == 0)], return_counts=True), 'mouth', np.unique(n[mo > 0], return_counts=True))
print('PROBE mw', list(b.matrix_world), 'parent', b.parent, 'uv', [l.name for l in me.uv_layers], 'attrs', [a.name for a in me.attributes if not a.name.startswith('.')])
print('PROBE objects', [(o.name, o.type) for o in bpy.data.objects])
