"""Texture-quality pass UVs (claude_shared/TEXTURE_QUALITY_PASS.md) on the installed Bone Dragon LOD0.

Imports the installed GLB, welds the glTF seam duplicates that share skin weights (so xatlas sees the connected
surface instead of the 2,853 Smart Topology islands), lays new charts with claude_shared/uv_atlas.py and writes:
- <out blend>: the welded LOD0 with the new UVMap (face attribute 'orig_face' = triangle index in the GLB primitive);
- <corner npz>: per original triangle its three corner UVs and positions (patch_glb_uvs.py rebuilds the GLB primitive);
- <upload glb>: the neutral static mesh for the Meshy retexture.
Geometry, weights and normals of the GLB are not touched; only the UVs are new.

Args: <installed glb> <out blend> <upload glb> <report json> <corner npz> [key=value uv_atlas.unwrap options]
"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
import uv_atlas

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, UPLOAD, REPORT, CORNERS = argv[:5]


def value(v):
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


options = {k: value(v) for k, v in (a.split('=', 1) for a in argv[5:])}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
body = bpy.data.objects['BoneDragon']
rig = next(m.object for m in body.modifiers if m.type == 'ARMATURE')
rig.animation_data_clear()
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()

me = body.data
n_faces = len(me.polygons)
attr = me.attributes.new('orig_face', 'INT', 'FACE')
attr.data.foreach_set('value', list(range(n_faces)))

bm = bmesh.new()
bm.from_mesh(me)
deform = bm.verts.layers.deform.active
classes = {}
for v in bm.verts:
    key = tuple(sorted((j, round(w, 6)) for j, w in v[deform].items() if w > 0))
    classes.setdefault(key, []).append(v)
before = len(bm.verts)
for verts in classes.values():
    if len(verts) > 1:
        bmesh.ops.remove_doubles(bm, verts=verts, dist=1e-6)
print('WELD', before, '->', len(bm.verts), 'verts;', len(bm.faces), 'faces')
assert len(bm.faces) == n_faces, 'weld dropped faces'
bm.to_mesh(me)
bm.free()

report = uv_atlas.unwrap(body, head_groups=('Head', 'Jaw'), head_factor=options.pop('head_factor', 1.8), **options)
print('UV_ATLAS', json.dumps(report))
json.dump(report, open(REPORT, 'w'), indent=1)

me = body.data
uv = me.uv_layers['UVMap'].data
orig = np.zeros(n_faces, np.int32)
me.attributes['orig_face'].data.foreach_get('value', orig)
U = np.zeros((n_faces, 3, 2), np.float32)
X = np.zeros((n_faces, 3, 3), np.float32)
for p in me.polygons:
    f = orig[p.index]
    for k, li in enumerate(p.loop_indices):
        U[f, k] = uv[li].uv
        X[f, k] = me.vertices[me.loops[li].vertex_index].co
np.savez(CORNERS, uv=U, xyz=X)
bpy.ops.wm.save_as_mainfile(filepath=OUT)

dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('UV done; upload', UPLOAD, n_faces)
