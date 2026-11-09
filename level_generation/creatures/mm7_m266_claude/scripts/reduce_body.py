"""Reduce the body and lofts of the grafted hydra after weighting (humanoid playbook: reduce after weights), heads
untouched: collapse decimation limited to a vertex group of body/loft vertices that touch no head face (the head
rings stay exact). Weights and attributes are interpolated by the collapse. Args: -- <in blend> <out blend> <ratio>"""
import bpy, sys, os
import numpy as np
src, out, ratio = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
ob = bpy.data.objects['Body']; me = ob.data
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
touch_head = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if part[p.index] > 0:
        touch_head[list(p.vertices)] = True
before = sum(len(p.vertices) - 2 for p in me.polygons)
g = ob.vertex_groups.new(name='_dec'); g.add([int(i) for i in np.nonzero(~touch_head)[0]], 1.0, 'REPLACE')
bpy.context.view_layer.objects.active = ob
for o in bpy.data.objects:
    o.select_set(o == ob)
mods = [(m.name, m.object) for m in ob.modifiers if m.type == 'ARMATURE']
for n, _ in mods:
    ob.modifiers.remove(ob.modifiers[n])
m = ob.modifiers.new('dec', 'DECIMATE'); m.vertex_group = '_dec'; m.ratio = float(ratio)
bpy.ops.object.modifier_apply(modifier=m.name)
ob.vertex_groups.remove(ob.vertex_groups['_dec'])
for n, o in mods:
    a = ob.modifiers.new(n, 'ARMATURE'); a.object = o
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
print('REDUCE', before, '->', sum(len(p.vertices) - 2 for p in me.polygons), 'body/loft',
      int((part == 0).sum()), 'heads', int((part > 0).sum()), 'unweighted', sum(1 for v in me.vertices if not v.groups))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
