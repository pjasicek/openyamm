import bpy, sys, json
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
print('PARTS', bpy.context.scene.get('pfem_parts'))
me = bpy.data.objects['Peasant'].data
p = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', p)
h = np.zeros(len(me.polygons), int); me.attributes['head'].data.foreach_get('value', h) if me.attributes['head'].domain=='FACE' else None
print('COUNTS', {int(k): int((p == k).sum()) for k in np.unique(p)}, 'head', int(h.sum()), me.attributes['head'].domain, me.attributes['head'].data_type)
arm = bpy.data.objects['Peasant_Rig']
print('ACTIONS', [a.name for a in bpy.data.actions])
