import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
names = {g.index: g.name for g in b.vertex_groups}
tot = {}
pa = np.zeros(len(me.vertices), int); me.attributes['part'].data.foreach_get('value', pa)
print('DBG parts', {int(k): int((pa == k).sum()) for k in np.unique(pa)})
for v in me.vertices:
    if pa[v.index] != 0: continue
    for g in v.groups: tot[names[g.group]] = tot.get(names[g.group], 0) + g.weight
print('DBG', sorted([(round(x, 1), k) for k, x in tot.items()], reverse=True)[:14])
