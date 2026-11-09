"""Step 1 cleanup for the pmn2 mage (Smart Topology v2, closed fists). Starts from work/v2_vis.blend (normalised to
1.578 m, soles z=0, facing -Y, loose parts P00..P14 with per-face outside visibility from analyse_parts.py).
Names parts, trims the eyeball shells to their visible front caps (centres kept in scene['pmn2_eyes']), decimates per
region (hidden faces and boots hard, face and fists untouched), keeps hidden skin under the cloth shells and joins
everything into one mesh 'Mage' with a per-face 'part' attribute. Saves work/step1_v1.blend."""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'v2_vis.blend'))
NAMES = {'P00': 'Body', 'P01': 'Head', 'P02': 'Hair', 'P03': 'Rope', 'P04': 'Mantle', 'P07': 'Skirt',
         'P10': 'RopeTailL', 'P11': 'RopeTailR', 'P14': 'RopeKnot', 'P12': 'EyeL', 'P13': 'EyeR'}
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    c = np.array([tuple(v.co) for v in o.data.vertices]).mean(0)
    if o.name in ('P05', 'P06'):
        o.name = 'HandRight' if c[0] < 0 else 'HandLeft'          # character right = -X (faces -Y)
    elif o.name in ('P08', 'P09'):
        o.name = 'PouchRight' if c[0] < 0 else 'PouchLeft'
    else:
        o.name = NAMES[o.name]
    o.data.materials.clear()
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


before = sum(tris(o) for o in P.values())
eyes = {}
for n in ('EyeL', 'EyeR'):                              # the head has no eye surface under them: keep the seen cap
    o = P[n]; c = np.array([tuple(v.co) for v in o.data.vertices])
    eyes[n] = {'centre': c.mean(0).tolist(), 'front_y': float(c[:, 1].min()), 'size': np.ptp(c, 0).tolist()}
    vis = list(o['visible'])
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    keep = {f.index for f in bm.faces if vis[f.index]}
    keep |= {g.index for f in bm.faces if f.index in keep for e in f.edges for g in e.link_faces}   # one ring margin
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data); bm.free()
bpy.context.scene['pmn2_eyes'] = json.dumps(eyes)


def hidden_verts(o):
    vis = list(o['visible'])
    seen = np.zeros(len(o.data.vertices), bool)
    for p in o.data.polygons:
        if vis[p.index]:
            seen[list(p.vertices)] = True
    return ~seen


for o in P.values():                                    # per-vertex hidden flag survives the collapses below
    a = o.data.attributes.new('hid', 'FLOAT', 'POINT'); a.data.foreach_set('value', hidden_verts(o).astype(float))


def hid(o):
    h = np.zeros(len(o.data.vertices)); o.data.attributes['hid'].data.foreach_get('value', h)
    return h > 0.5


def decimate(o, passes):
    """passes: [(face predicate(centre, all_verts_hidden, touches_boundary), ratio)]; each pass collapses only the
    selected faces in edit mode, so unselected regions (face, fists, rims) keep every vertex."""
    for x in bpy.data.objects:
        x.select_set(x == o)
    bpy.context.view_layer.objects.active = o
    for pred, ratio in passes:
        h = hid(o)
        bm = bmesh.new(); bm.from_mesh(o.data)
        bnd = {v.index for e in bm.edges if e.is_boundary for v in e.verts}
        sel = [all(h[v.index] for v in f.verts) for f in bm.faces]
        flags = [pred(f.calc_center_median(), sel[f.index], any(v.index in bnd for v in f.verts)) for f in bm.faces]
        bm.free()
        o.data.polygons.foreach_set('select', flags); o.data.update()
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.decimate(ratio=ratio)
        bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')


ALL = lambda c, h, b: True
decimate(P['Body'], [(lambda c, h, b: h and not b, 0.30),
                     (lambda c, h, b: not h and 0.04 < c.z < 0.34, 0.50),            # boot shafts/feet
                     (lambda c, h, b: not h and 0.43 < c.z < 0.68 and abs(c.x) < 0.26, 0.62),   # trousers
                     (lambda c, h, b: not h and c.z > 0.70 and not b, 0.72)])           # vest, arms
decimate(P['Head'], [(lambda c, h, b: h and not b, 0.20),
                     (lambda c, h, b: not h and not b and not (c.y < -0.03 and c.z > 1.36), 0.7)])
decimate(P['Hair'], [(lambda c, h, b: not b and h, 0.25), (lambda c, h, b: not b and not h and c.y > -0.02, 0.33)])
decimate(P['Mantle'], [(lambda c, h, b: not b, 0.70)])
decimate(P['Rope'], [(ALL, 0.28)])
for n in ('RopeTailL', 'RopeTailR'):
    decimate(P[n], [(ALL, 0.40)])
decimate(P['RopeKnot'], [(ALL, 0.50)])
for n in ('PouchLeft', 'PouchRight'):
    decimate(P[n], [(ALL, 0.31)])


def tuck(inner, outer, gap, zr, back=0.02):
    """Inner-shell vertices just outside (< gap) or slightly through (< back) the outer shell move to gap below it."""
    o = P[outer]; me = P[inner].data
    tree = BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices], [tuple(p.vertices) for p in o.data.polygons])
    me.update(); moved = 0; h = hid(P[inner])
    for v in me.vertices:
        if not h[v.index] or not (zr[0] < v.co.z < zr[1]):
            continue
        n = v.normal.copy()
        out = tree.ray_cast(v.co + n * 1e-5, n, gap)
        inn = tree.ray_cast(v.co - n * 1e-5, -n, back)
        if out[0] is not None:
            v.co = out[0] - n * gap; moved += 1
        elif inn[0] is not None:
            v.co = inn[0] - n * gap; moved += 1
    me.update()
    return moved


tucked = {'Body<Mantle': tuck('Body', 'Mantle', 0.008, (1.0, 1.36)),
          'Head<Hair': tuck('Head', 'Hair', 0.005, (1.30, 1.60)),
          'Body<Skirt': tuck('Body', 'Skirt', 0.008, (0.62, 0.97)),
          'Body<Rope': tuck('Body', 'Rope', 0.004, (0.86, 0.98)),
          'Skirt<Rope': tuck('Skirt', 'Rope', 0.003, (0.86, 0.98))}

after = {n: tris(o) for n, o in P.items()}
ORDER = ['Body', 'Head', 'EyeL', 'EyeR', 'Hair', 'Mantle', 'Skirt', 'HandRight', 'HandLeft', 'Rope', 'RopeKnot', 'RopeTailL',
         'RopeTailR', 'PouchRight', 'PouchLeft']
for n in ORDER:
    o = P[n]
    if 'visible' in o.keys():
        del o['visible']
    a = o.data.attributes.new('part', 'INT', 'FACE')
    a.data.foreach_set('value', [ORDER.index(n)] * len(o.data.polygons))
    for p in o.data.polygons:
        p.use_smooth = True
for x in bpy.data.objects:
    x.select_set(x.type == 'MESH')
bpy.context.view_layer.objects.active = P['Body']
bpy.ops.object.join()
mage = bpy.context.view_layer.objects.active; mage.name = 'Mage'; mage.data.name = 'Mage'
bpy.context.scene['pmn2_parts'] = json.dumps(ORDER)
report = {'before': before, 'after': after, 'total_after': sum(after.values()), 'tucked_verts': tucked}
json.dump(report, open(os.path.join(common.WORK, 'step1_report.json'), 'w'), indent=1)
print('STEP1', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
