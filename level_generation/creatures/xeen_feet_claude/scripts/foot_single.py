"""One winged RIGHT foot (toes -Y, medial side +X): reduce the 0.26 m Smart Topology foot to about 2,900 triangles
(foot body and the two wings decimated separately), triangulate, unwrap with claude_shared/uv_atlas.py (toes 1.4x
denser) and export the static Meshy upload texturing/foot_upload.glb.
Vertex groups: Foot (body, ankle bumps), Toes (a gradient over the ball of the foot, 0 behind y=-0.068, 1 in front of
y=-0.094), WingIn (+X, the medial wing, piece 1), WingOut (-X, the lateral wing, pieces 2-3).
Saves work/foot_uv.blend and work/foot_hinges.json (wing roots, ankle centre, ball line).
Refuses to overwrite an existing upload (a paint may belong to it). Args: -- [foot ratio] [wing ratio]"""
import bpy, os, sys, json, bmesh
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared'))
import uv_atlas
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FOOT_RATIO = float(a[0]) if a else 0.18
WING_RATIO = float(a[1]) if len(a) > 1 else 0.20
DRY = len(a) > 2 and a[2] == 'dry'
UPLOAD = os.path.join(HERE, 'texturing', 'foot_upload.glb')
if os.path.exists(UPLOAD) and not DRY:
    raise SystemExit('texturing/foot_upload.glb exists')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'foot_clean.blend'))
m = bpy.data.objects['Foot']
d = np.load(os.path.join(HERE, 'work', 'foot_pieces.npz')); lab = d['label']; co = d['co']
PIECE_GROUP = {0: 'Foot', 4: 'Foot', 1: 'WingIn', 2: 'WingOut', 3: 'WingOut'}
foot = co[lab == 0]
ankle = foot[foot[:, 2] > foot[:, 2].max() - 0.03]
ankle_c = [float(ankle[:, 0].mean()), float(ankle[:, 1].mean())]
hinges = {}
for name in ('WingIn', 'WingOut'):
    c = co[np.isin(lab, [p for p, g in PIECE_GROUP.items() if g == name])]
    r = np.hypot(c[:, 0] - ankle_c[0], c[:, 1] - ankle_c[1])
    hinges[name] = c[np.argsort(r)[:16]].mean(0).tolist()          # the root: the wing's points nearest the ankle axis
    tip = c[np.argmax(r)]
    hinges[name + '_tip'] = tip.tolist()
TOE0, TOE1 = -0.068, -0.094                                          # ball of the foot: weight ramps 0 -> 1
groups = {n: m.vertex_groups.new(name=n) for n in ('Foot', 'Toes', 'WingIn', 'WingOut')}
for v in m.data.vertices:
    g = PIECE_GROUP[int(lab[v.index])]
    if g == 'Foot':
        t = min(1.0, max(0.0, (TOE0 - v.co.y) / (TOE0 - TOE1)))
        t = t * t * (3 - 2 * t)
        if t < 1: groups['Foot'].add([v.index], 1.0 - t, 'REPLACE')
        if t > 0: groups['Toes'].add([v.index], t, 'REPLACE')
    else:
        groups[g].add([v.index], 1.0, 'REPLACE')
# per-part decimation: split by group, collapse, join back
bpy.context.view_layer.objects.active = m
for o in bpy.data.objects: o.select_set(o == m)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
wing_idx = {groups['WingIn'].index, groups['WingOut'].index}
for p in m.data.polygons:
    p.select = any(g.group in wing_idx for g in m.data.vertices[p.vertices[0]].groups)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
wings = next(o for o in bpy.data.objects if o.type == 'MESH' and o is not m)
t0 = len(m.data.polygons) + len(wings.data.polygons)
counts = {}
for o, ratio in ((m, FOOT_RATIO), (wings, WING_RATIO)):
    for x in bpy.data.objects: x.select_set(x == o)
    bpy.context.view_layer.objects.active = o
    before = sum(len(p.vertices) - 2 for p in o.data.polygons)
    dec = o.modifiers.new('dec', 'DECIMATE'); dec.decimate_type = 'COLLAPSE'; dec.ratio = ratio
    dec.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='dec')
    tri = o.modifiers.new('tri', 'TRIANGULATE'); bpy.ops.object.modifier_apply(modifier='tri')
    counts[o.name] = (before, len(o.data.polygons))
for x in bpy.data.objects: x.select_set(x in (m, wings))
bpy.context.view_layer.objects.active = m
bpy.ops.object.join()
print('REDUCED', t0, '->', len(m.data.polygons), counts)
if DRY:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'foot_dry.blend'))
    raise SystemExit
report = uv_atlas.unwrap(m, head_groups=('Toes',), head_factor=1.4)
print('UV', report.get('use'), report.get('charts_used'), report.get('packer_used'), report.get('fallbacks'))
json.dump({'hinges': hinges, 'ankle': ankle_c, 'ball': [TOE0, TOE1],
           'uv': {k: report.get(k) for k in ('use', 'charts_used', 'packer_used', 'fallbacks')}},
          open(os.path.join(HERE, 'work', 'foot_hinges.json'), 'w'), indent=1, default=str)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'foot_uv.blend'))
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
for o in bpy.data.objects: o.select_set(o == m)
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('UPLOAD foot', len(m.data.polygons))
