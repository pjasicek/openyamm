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
# Moon Cleric (15.3k -> ~9.9k): per GARMENT (prepare_rig.py); the face skin is protected, the claws are not (1.1k
# triangles each from Smart Topology); eyes and cheek plates are kept as they are
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
TARGET = {int(k): v for k, v in cfg.C['reduce'].items()}
ALIAS = {int(k): v for k, v in cfg.C.get('reduce_alias', {}).items()}   # necromancer: the tight hem (17) is reduced with the cape (2), as before it was split off
before = sum(len(p.vertices) - 2 for p in me.polygons)
names = [g.name for g in body.vertex_groups]
# aliased garments (necromancer: tight hem 17 reduced with the cape 2): the collapse interpolates the INT 'garment'
# attribute across a 17/2 edge (stray labels 5-16 appeared, three of them pulled cape faces into the head set), so the
# alias is carried as a float flag and the garment is restored after the join
ALIAS0 = {int(k): v for k, v in cfg.C.get('reduce_alias', {}).items()}
if ALIAS0:
    g0 = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', g0)
    for k_ in ALIAS0:
        fl = me.attributes.new(f'_alias{k_}', 'FLOAT', 'POINT'); fl.data.foreach_set('value', (g0 == k_).astype(np.float32))
    me.attributes['garment'].data.foreach_set('value', np.array([ALIAS0.get(int(x), int(x)) for x in g0], np.int32))
prot = body.vertex_groups.new(name='_protect')
keys = [i for i, n in enumerate(names) if n in ('B_Head', 'B_Neck')]
pv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', pv)
for v in me.vertices:
    w = sum(e.weight for e in v.groups if e.group in keys)
    if w > 0.3 and pv[v.index] == 0:                       # only the face SKIN
        prot.add([v.index], 1.0, 'REPLACE')
# small loose pieces (beads, collar bars, tassels: < SMALL triangles) are kept whole; decimating their garment together
# collapsed seven of them below 4 triangles
SMALL = 60
pc0 = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pc0)
ptris = {}
for f in me.polygons:
    k = int(pc0[f.vertices[0]]); ptris[k] = ptris.get(k, 0) + len(f.vertices) - 2
small = {k for k, n in ptris.items() if n < SMALL}
for v in me.vertices:
    if int(pc0[v.index]) in small:
        prot.add([v.index], 1.0, 'REPLACE')
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
parts = {}
for p, tgt in TARGET.items():
    for v in me.vertices:
        v.select = bool(ALIAS.get(int(pv[v.index]), int(pv[v.index])) == p)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    me = body.data
    pv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', pv)
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
for k_ in ALIAS0:
    fl = np.zeros(len(me.vertices), np.float32); me.attributes[f'_alias{k_}'].data.foreach_get('value', fl)
    g0 = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', g0)
    g0[fl > 0.5] = k_; me.attributes['garment'].data.foreach_set('value', g0); me.attributes.remove(me.attributes[f'_alias{k_}'])
pc = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pc)
per = {}
for f in me.polygons:
    k = int(pc[f.vertices[0]]); per[k] = per.get(k, 0) + len(f.vertices) - 2
thin = sorted(k for k, n in per.items() if n < 4)
print('REDUCE pieces', len(per), 'with < 4 tris:', len(thin), thin[:20])
print('REDUCE', {p: f'{a}->{b}' for p, (a, b) in report.items()}, 'total', before, '->', sum(len(f.vertices) - 2 for f in body.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
