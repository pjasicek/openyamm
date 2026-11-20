"""Second triangle cut on the textured master (rig_v6: final weights, head UVs), user review "reduce tris" 2026-10-20:
9,967 -> ~7,000 body triangles. Collapse decimation per piece interpolates the UV layers and vertex groups. Protected
(vertex group factor 0): the bony hands and fingers (hand/finger weight > 0.3: the staff grip and its clearance gate)
and the shoes (the only visible part of the legs, z < 0.14); the legs above the shoes are hidden by the floor-length
skirt and take the deepest cut. Meshy's body UV layout is too fragmented to keep through a collapse (on the chain mail
1,850 of its vertices sit on seams; the skirt smeared and opened slivers), so rebake_body_uv.py then gives the body a
new UVMap and bakes the textures from the unreduced copy this script keeps (work/rig_v6_full.blend). The head set
(its own smart-projected HeadUV, smooth paint) keeps its textures through the collapse.
Runs once on the textured master, guarded by an object property. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
if body.get('reduced_textured'):
    print('REDUCE2 already applied')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out)); sys.exit(0)
# piece -> target triangles (pieces: 100 skull + coif, 101 crown, 102 crown band, 103+ studs (kept), 1/2 arms with
# hands, 5 skirt, 4 legs + shoes, 7 breastplate, 8/9 pauldrons, 11 abdomen, 12/13 cuffs, 14 belt, 15 buckle,
# 19/20 chain shoulder caps, 21 band)
TARGET = {100: 1200, 101: 560, 102: 160, 1: 950, 2: 920, 5: 700, 4: 260, 7: 380, 8: 300, 9: 300, 11: 200,
          12: 160, 13: 160, 14: 160, 15: 100, 19: 90, 20: 85, 21: 80}
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
before = sum(len(p.vertices) - 2 for p in me.polygons)
names = [g.name for g in body.vertex_groups]
HANDS = [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n or 'Thumb' in n]
co = np.array([tuple(v.co) for v in me.vertices])
hand_w = np.zeros(len(me.vertices))
for v in me.vertices:
    hand_w[v.index] = sum(e.weight for e in v.groups if e.group in HANDS)
keep = (np.isin(pv, (1, 2)) & (hand_w > 0.3)) | ((pv == 4) & (co[:, 2] < 0.14))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(out)), 'rig_v6_full.blend'), copy=True)
prot = body.vertex_groups.new(name='_protect')
for i in np.where(keep)[0]:
    prot.add([int(i)], 1.0, 'REPLACE')
print('REDUCE2 protected vertices: hands', int((np.isin(pv, (1, 2)) & (hand_w > 0.3)).sum()),
      'shoes', int(((pv == 4) & (co[:, 2] < 0.14)).sum()))
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
parts = {}
for p in TARGET:
    me = body.data
    pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for v in me.vertices:
        v.select = bool(pv[v.index] == p)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    parts[p] = [o for o in bpy.context.selected_objects if o is not body][-1]
    for o in bpy.data.objects:
        o.select_set(o == body)
report = {}
for p, o in parts.items():
    tris = sum(len(f.vertices) - 2 for f in o.data.polygons)
    if tris > TARGET[p]:
        m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = TARGET[p] / tris
        m.vertex_group = '_protect'; m.invert_vertex_group = True; m.vertex_group_factor = 1.0
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
body['reduced_textured'] = True
after = sum(len(f.vertices) - 2 for f in body.data.polygons)
print('REDUCE2', {p: f'{a}->{b}' for p, (a, b) in report.items()}, 'total', before, '->', after)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
