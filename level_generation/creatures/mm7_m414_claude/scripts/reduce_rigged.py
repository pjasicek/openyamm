"""Triangle budget AFTER the weights (TEST_DRIVE.md: reducing before the Meshy weight transfer moved vertices up to
23 mm, mismatched weights and pushed the attack's arm stretch from 4.3x to 9.7x). Collapse decimation interpolates
vertex groups, so the finished weights survive. Per shell (piece) targets; on the skin the head (Head/Neck weight
> 0.3) and the hands (hand/finger weight > 0.3) are protected. Shells are separated, reduced and joined back with
the armature modifier. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
# m414 15.45k -> ~10.3k; natm (14.3k -> ~9.3k): per GARMENT (garments.py), the skin with head and hands protected; feather cards decimate together
# (collapse keeps each card's outline; a card left with < 4 triangles is reported)
TARGET = {0: 7400, 1: 1300, 6: 1200}                               # m414 (weights_fix.py labels; 15.45k in): belt kept
before = sum(len(p.vertices) - 2 for p in me.polygons)
names = [g.name for g in body.vertex_groups]
prot = body.vertex_groups.new(name='_protect')
keys = [i for i, n in enumerate(names) if n in ('B_Head', 'B_Neck') or 'Hand' in n or 'Finger' in n]
pv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', pv)
rg = pv.copy()
me.attributes.new('rgroup', 'INT', 'POINT').data.foreach_set('value', rg)
for v in me.vertices:
    w = sum(e.weight for e in v.groups if e.group in keys)
    if w > 0.3 and pv[v.index] == 0:                       # only the face/hand SKIN; teeth and ear hoops ride the head
        prot.add([v.index], 1.0, 'REPLACE')
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
parts = {}
for p, tgt in TARGET.items():
    for v in me.vertices:
        v.select = bool(rg[v.index] == p)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    me = body.data
    rg = np.zeros(len(me.vertices), np.int32); me.attributes['rgroup'].data.foreach_get('value', rg)
    new = [o for o in bpy.context.selected_objects if o is not body]
    parts[p] = new[-1]
    for o in bpy.data.objects:
        o.select_set(o == body)
report = {}
for p, o in parts.items():
    tris = sum(len(f.vertices) - 2 for f in o.data.polygons)
    if tris > TARGET[p]:
        m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = TARGET[p] / tris
        m.vertex_group = '_protect'; m.invert_vertex_group = True
        bpy.context.view_layer.objects.active = o
        for x in bpy.data.objects:
            x.select_set(x == o)
        bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
        bpy.ops.object.modifier_apply(modifier='dec')
    report[p] = (tris, sum(len(f.vertices) - 2 for f in o.data.polygons))
for x in bpy.data.objects:
    x.select_set(x is body or x in parts.values())
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.vertex_groups.remove(body.vertex_groups['_protect'])
me = body.data
me.attributes.remove(me.attributes['rgroup'])
pc = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pc)
per = {}
for f in me.polygons:
    k = int(pc[f.vertices[0]]); per[k] = per.get(k, 0) + len(f.vertices) - 2
thin = sorted(k for k, n in per.items() if n < 4)
print('REDUCE pieces', len(per), 'with < 4 tris:', len(thin), thin[:20])
print('REDUCE', {p: f'{a}->{b}' for p, (a, b) in report.items()}, 'total', before, '->', sum(len(f.vertices) - 2 for f in body.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
