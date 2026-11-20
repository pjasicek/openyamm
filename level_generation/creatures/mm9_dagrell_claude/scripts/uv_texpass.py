"""Texture quality pass UVs for the Dagrell (claude_shared/TEXTURE_QUALITY_PASS.md, 2026-10-30).

work/uv_v6.blend (after repivot_dagrell.py) is the installed mesh: 136 separate bone pieces, Smart UV layout (12 % of the
atlas, 1,448 islands, 43 % of the surface on fragments). Mesh, weights and rig stay; only UVMap changes.

- Both left limbs are mirrors of the right ones and share their texels (old UVs identical): they keep sharing, so
  claude_shared/uv_atlas.py only lays out the other 6,140 faces, and each left face gets its twin's new UVs corner by
  corner (matched through the old UVs).
- Charts are cut and flattened on the FitPose shape (Meshy's own geometry, what the HD views show, and close to
  Standing), not the crouched bind, which pulls the joint-spanning pieces apart.
- Upload (neutral static GLB, UVMap only): the whole body in the FitPose as uv_export.py; left limbs collapsed to one UV
  point (zero area), so Meshy spends no texels on them but they still occlude the torso in its projection.

Args: <in blend> <out blend> <upload glb> <report json> [key=value uv_atlas.unwrap options]
Never re-run once its upload went to Meshy (xatlas packs differently per run).
"""
import bpy, bmesh, sys, os, json
from collections import defaultdict
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
import uv_atlas

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD, REPORT = argv[:4]
options = {k: (float(v) if v.replace('.', '', 1).isdigit() and '.' in v else int(v) if v.isdigit() else v)
           for k, v in (a.split('=', 1) for a in argv[4:])}
HEAD = ('Xheadpiv', 'Xjawbase', 'Xjawpiv', 'Xnose')
DUMP = (0.25 / 2048, 0.25 / 2048)

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
me = body.data


def set_fitpose():
    fp = bpy.data.actions['FitPose']
    rig.animation_data_create()
    rig.animation_data.action = fp
    try:
        rig.animation_data.action_slot = fp.slots[0]
    except Exception:
        pass
    sc.frame_set(0)
    bpy.context.view_layer.update()


def set_rest():
    rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
    bpy.context.view_layer.update()


n_f = len(me.polygons)
loop_start = np.array([p.loop_start for p in me.polygons])
assert all(len(p.vertices) == 3 for p in me.polygons)
old = np.zeros(len(me.loops) * 2, np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', old)
old = old.reshape(-1, 2)
face_old = old[(loop_start[:, None] + np.arange(3)).ravel()].reshape(n_f, 3, 2)

# ---- left limb faces: bones of the -x side (mirror pairs in the rig), twin = the face with identical old UVs
heads = {b.name: b.head_local.copy() for b in rig.data.bones}
mid = float(np.median([h.x for h in heads.values()]))
tri = np.array([p.vertices[:] for p in me.polygons])
key = defaultdict(list)
for f in range(n_f):
    key[tuple(sorted(map(tuple, np.round(face_old[f], 6))))].append(f)
pairs = [v for v in key.values() if len(v) > 1]
assert all(len(v) == 2 for v in pairs), 'old UV shared by more than two faces'
rest_x = np.array([v.co.x for v in me.vertices])
twin = {}
for a, b in pairs:
    l, r = (a, b) if rest_x[tri[a]].mean() < rest_x[tri[b]].mean() else (b, a)
    twin[l] = r
left = np.zeros(n_f, bool)
left[list(twin)] = True
report = {'faces': n_f, 'left_shared': int(left.sum())}

# ---- working copy: faces with their own texels only, vertices at the FitPose
set_fitpose()
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg).to_mesh()
fit_co = np.zeros(len(ev.vertices) * 3, np.float32)
ev.vertices.foreach_get('co', fit_co)
body.evaluated_get(dg).to_mesh_clear()
set_rest()
ov = me.attributes.new('tp_orig_v', 'INT', 'POINT')
ov.data.foreach_set('value', np.arange(len(me.vertices), dtype=np.int32))
of = me.attributes.new('tp_orig_f', 'INT', 'FACE')
of.data.foreach_set('value', np.arange(n_f, dtype=np.int32))
half = body.copy()
half.data = me.copy()
half.modifiers.clear()
half.parent = None
half.name = 'TexpassUnique'
half.data.vertices.foreach_set('co', fit_co)
half.data.update()
sc.collection.objects.link(half)
bm = bmesh.new()
bm.from_mesh(half.data)
layer = bm.faces.layers.int['tp_orig_f']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if left[f[layer]]], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(half.data)
bm.free()
half.data.update()
uv_report = uv_atlas.unwrap(half, head_groups=HEAD, head_factor=1.8, **options)
report['uv_atlas'] = uv_report
print('UV_ATLAS', json.dumps(uv_report))

# ---- new UVs back: own faces by original vertex, left faces through the old UVs of their twin
hm = half.data
huv = np.zeros(len(hm.loops) * 2, np.float32)
hm.uv_layers['UVMap'].data.foreach_get('uv', huv)
huv = huv.reshape(-1, 2)
horig_v = np.zeros(len(hm.vertices), np.int32)
hm.attributes['tp_orig_v'].data.foreach_get('value', horig_v)
horig_f = np.zeros(len(hm.polygons), np.int32)
hm.attributes['tp_orig_f'].data.foreach_get('value', horig_f)
new = old.copy()
filled = np.zeros(n_f, bool)
for p in hm.polygons:
    f = int(horig_f[p.index])
    table = {int(horig_v[v]): huv[li] for v, li in zip(p.vertices, p.loop_indices)}
    for k in range(3):
        new[loop_start[f] + k] = table[int(tri[f][k])]
    filled[f] = True
worst = 0.0
for l, r in twin.items():
    for k in range(3):
        d = np.abs(face_old[r] - face_old[l][k]).sum(1)
        j = int(np.argmin(d))
        worst = max(worst, float(d[j]))
        new[loop_start[l] + k] = new[loop_start[r] + j]
    filled[l] = True
assert filled.all()
report['twin_worst_old_uv'] = worst
assert worst < 1e-5, worst
bpy.data.objects.remove(half)
bpy.data.meshes.remove(hm)
me.attributes.remove(me.attributes['tp_orig_v'])
me.attributes.remove(me.attributes['tp_orig_f'])
me.uv_layers['UVMap'].data.foreach_set('uv', new.ravel())
me.update()

# ---- fragments as texture_quality.py counts them (islands: faces joined across edges with equal UVs)
own = np.nonzero(~left)[0]
parent = list(range(n_f))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


new_face = new[(loop_start[:, None] + np.arange(3)).ravel()].reshape(n_f, 3, 2)
edge = {}
for f in own:
    for k in range(3):
        a, b = int(tri[f][k]), int(tri[f][(k + 1) % 3])
        ka = (min(a, b), max(a, b))
        uvs = tuple(sorted((tuple(np.round(new_face[f][k], 6)), tuple(np.round(new_face[f][(k + 1) % 3], 6)))))
        other = edge.get((ka, uvs))
        if other is None:
            edge[(ka, uvs)] = int(f)
        else:
            parent[find(int(f))] = find(other)
roots = np.array([find(int(f)) for f in own])
pos = np.array([v.co for v in me.vertices])
pt = pos[tri[own]]
area = np.linalg.norm(np.cross(pt[:, 1] - pt[:, 0], pt[:, 2] - pt[:, 0]), axis=1) / 2
_, inverse, counts = np.unique(roots, return_inverse=True, return_counts=True)
report['islands'] = len(counts)
report['fragment_islands'] = int((counts < 8).sum())
report['fragment_surface_pct'] = round(float(100 * area[counts[inverse] < 8].sum() / area.sum()), 2)
print('ISLANDS', report['islands'], 'fragments', report['fragment_islands'], report['fragment_surface_pct'], '%')

json.dump(report, open(REPORT, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)

# ---- upload
set_fitpose()
dg = bpy.context.evaluated_depsgraph_get()
posed = bpy.data.meshes.new_from_object(body.evaluated_get(dg))
dup = bpy.data.objects.new('DagrellUpload', posed)
dup.matrix_world = body.matrix_world
sc.collection.objects.link(dup)
duv = posed.uv_layers['UVMap'].data
for p in posed.polygons:
    if left[p.index]:
        for li in p.loop_indices:
            duv[li].uv = DUMP
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('TEXPASS_UV', json.dumps({k: v for k, v in report.items() if k != 'uv_atlas'}))
