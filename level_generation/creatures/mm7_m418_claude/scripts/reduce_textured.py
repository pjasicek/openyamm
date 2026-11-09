"""Second triangle cut on the textured master (rig_v6: final weights; user review "reduce tris" 2026-10-20, after the
m270 lich). Collapse decimation per garment (scripts/reduce2.json 'targets': garment -> triangles) interpolates the
UV layers and vertex groups; both texture sets are then given new UVs and rebaked from the unreduced copy this script
keeps (work/rig_v6_full.blend) by rebake_uv.py, so texture seams need no protection (Meshy's fragmented layouts do not
survive a collapse: the lich's chain mail smeared and its skirt opened slivers). Protected (decimate vertex group,
factor 0): vertices on the head/body boundary (the face split between the two texture sets stays where it is), and
vertices weighted over 'protect_w' to a bone whose name contains one of 'protect' (hands, fingers, claws). Head-set
vertices get 'head_w' (partly protected: faces carry the most detail).
Runs once on the textured master, guarded by an object property. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(HERE, 'scripts', 'reduce2.json')))
TARGET = {int(k): v for k, v in CFG['targets'].items()}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
if body.get('reduced_textured'):
    print('REDUCE2 already applied')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out)); sys.exit(0)
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
before = sum(len(p.vertices) - 2 for p in me.polygons)
names = [g.name for g in body.vertex_groups]
PB = [i for i, n in enumerate(names) if any(k in n for k in CFG['protect'])]
pw = np.zeros(len(me.vertices)); hv = np.zeros(len(me.vertices), bool); bv = np.zeros(len(me.vertices), bool)
for v in me.vertices:
    pw[v.index] = sum(e.weight for e in v.groups if e.group in PB)
for p in me.polygons:
    (hv if hd[p.index] else bv)[list(p.vertices)] = True
# head_w on the head set's vertices (head_w_garments: only those garments; m418: the skin, not the separate teeth)
hg = np.isin(gv, CFG['head_w_garments']) if 'head_w_garments' in CFG else np.ones(len(gv), bool)
w = np.where(hv & hg, float(CFG.get('head_w', 0.0)), 0.0)
w[pw > CFG.get('protect_w', 0.3)] = 1.0
w[hv & bv] = 1.0
# creases (reduce2.json crease_r > 0): a vertex with an opposite-facing surface within crease_r (armpits, the hump beside
# the arm, lips): a collapse across the gap moved the surface so the bake rays met the other side (m418: a dark patch
# where the arm meets the shoulder)
CR = float(CFG.get('crease_r', 0))
crease = np.zeros(len(me.vertices), bool)
if CR > 0:
    from mathutils.kdtree import KDTree
    co = [v.co.copy() for v in me.vertices]; nr = [v.normal.copy() for v in me.vertices]
    kd = KDTree(len(co))
    for i, c in enumerate(co):
        kd.insert(c, i)
    kd.balance()
    for i, c in enumerate(co):
        for _, j, d in kd.find_range(c, CR):
            if nr[i].dot(nr[j]) < -0.3 and (co[j] - c).dot(nr[i]) > 0:
                crease[i] = True; break
    w[crease] = 1.0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(out)), 'rig_v6_full.blend'), copy=True)
prot = body.vertex_groups.new(name='_protect')
for i in np.where(w > 0)[0]:
    prot.add([int(i)], float(w[i]), 'REPLACE')
print('REDUCE2 protected vertices: creases', int(crease.sum()), 'bones', int((pw > CFG.get('protect_w', 0.3)).sum()), 'head/body boundary',
      int((hv & bv).sum()), 'head (partly)', int(hv.sum()))
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
parts = {}
for g in TARGET:
    me = body.data
    gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
    if not (gv == g).any():
        continue
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for v in me.vertices:
        v.select = bool(gv[v.index] == g)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    parts[g] = [o for o in bpy.context.selected_objects if o is not body][-1]
    for o in bpy.data.objects:
        o.select_set(o == body)
report = {}
for g, o in parts.items():
    tris = sum(len(f.vertices) - 2 for f in o.data.polygons)
    if tris > TARGET[g]:
        m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = TARGET[g] / tris
        m.vertex_group = '_protect'; m.invert_vertex_group = True; m.vertex_group_factor = 1.0
        bpy.context.view_layer.objects.active = o
        for x in bpy.data.objects:
            x.select_set(x == o)
        bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
        bpy.ops.object.modifier_apply(modifier='dec')
    report[g] = (tris, sum(len(f.vertices) - 2 for f in o.data.polygons))
for x in bpy.data.objects:
    x.select_set(x is body or x in parts.values())
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.vertex_groups.remove(body.vertex_groups['_protect'])
body['reduced_textured'] = True
after = sum(len(f.vertices) - 2 for f in body.data.polygons)
print('REDUCE2', {g: f'{a}->{b}' for g, (a, b) in report.items()}, 'total', before, '->', after)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
