"""Texture-quality pass UVs on the head-fixed master (claude_shared/TEXTURE_QUALITY_PASS.md): uv_v2.blend -> uv_v3.blend.
Replaces the Smart UV layout and the head fix's 0.9 squeeze and top band with xatlas charts packed by
claude_shared/uv_atlas.py, head charts x1.4 as before. Mesh, weights and attributes are unchanged.

The mouth bag keeps its own unwrap: head_fix.py laid its rectangle out at a half-open reference pose, so its texels stay
within about 2x at the widest opening, which a bind-pose chart would lose. Bag faces (attribute mouth_bag) are kept out of
the charts and join the packing as two islands of their own (cavity, throat cap), at the head's density, by wrapping the
'pack' call of uv_atlas. The relocated faces of the head fix simply become part of the body charts again.

Args: <uv_v2 blend> <out blend> <upload glb> <report json> [key=value uv_atlas.unwrap options]
Also writes work/uv_v3_bag.npz (old and new UVs of the bag and relocated faces; texpass_tex.py paints through them).
"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
import uv_atlas

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD, REPORT = argv[:4]
options = {k: (float(v) if v.replace('.', '', 1).isdigit() and '.' in v else int(v) if v.isdigit() else v)
           for k, v in (a.split('=', 1) for a in argv[4:])}
HEAD = ('Bip01 Head', 'Bone35', 'Bone36', 'Bone37', 'Bone38', 'Bone39', 'Bone40', 'Bone41')
HEAD_FACTOR = 1.4
OLD_TEXELS_PER_METRE = 300.0            # head_fix.py DENSITY at 2K, no reduction applied ('relocated_scale' n/a to the bag)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
mesh = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = mesh.data
n = len(me.polygons)
bag = np.array([d.value for d in me.attributes['mouth_bag'].data])
rel = np.array([d.value for d in me.attributes['relocated'].data])
flat = np.zeros(len(me.loops) * 2, np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', flat)
flat = flat.reshape(-1, 2)
assert all(p.loop_total == 3 for p in me.polygons)
UV0 = np.array([flat[list(p.loop_indices)] for p in me.polygons], np.float64)
tri = np.array([p.vertices[:] for p in me.polygons], np.int32)

# the body without the bag
tmp = mesh.copy()
tmp.data = me.copy()
tmp.modifiers.clear()
tmp.parent = None
tmp.matrix_world = mesh.matrix_world
bpy.context.scene.collection.objects.link(tmp)
bm = bmesh.new()
bm.from_mesh(tmp.data)
bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if bag[f.index]], context='FACES_ONLY')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(tmp.data)
bm.free()
tmp.data.update()
keep = np.nonzero(bag == 0)[0]
assert len(tmp.data.polygons) == len(keep)
for i in (0, len(keep) // 2, len(keep) - 1):        # bmesh keeps the face order
    assert np.allclose([tmp.data.vertices[v].co[:] for v in tmp.data.polygons[i].vertices],
                       [me.vertices[v].co[:] for v in tri[keep[i]]])

bag_faces = np.nonzero(bag)[0]
bag_uv = UV0[bag_faces] * 2048.0 / OLD_TEXELS_PER_METRE * HEAD_FACTOR
pack_call = uv_atlas._xatlas
packed_bag = {}


def with_bag(mode, inputs, *rest):
    if mode != 'pack':
        return pack_call(mode, inputs, *rest)
    uv, vert = inputs['uv'], inputs['vert']
    both = {'uv': np.concatenate([uv, bag_uv.astype(uv.dtype)]),
            'vert': np.concatenate([vert, tri[bag_faces] + vert.max() + 1])}
    out = pack_call('pack', both, *rest)
    packed_bag['uv'] = out['uv'][len(uv):]
    return {'uv': out['uv'][:len(uv)]}


uv_atlas._xatlas = with_bag
report = uv_atlas.unwrap(tmp, head_groups=HEAD, head_factor=HEAD_FACTOR, **options)
print('UV_ATLAS', json.dumps(report))
flat2 = np.zeros(len(tmp.data.loops) * 2, np.float32)
tmp.data.uv_layers['UVMap'].data.foreach_get('uv', flat2)
flat2 = flat2.reshape(-1, 2)
UV1 = UV0.copy()
UV1[keep] = np.array([flat2[list(p.loop_indices)] for p in tmp.data.polygons], np.float64)
UV1[bag_faces] = packed_bag['uv']
out = np.zeros_like(flat)
for p in me.polygons:
    out[list(p.loop_indices)] = UV1[p.index]
me.uv_layers['UVMap'].data.foreach_set('uv', out.ravel())
me.update()
bpy.data.objects.remove(tmp)
area = lambda u: np.abs((u[:, 1, 0] - u[:, 0, 0]) * (u[:, 2, 1] - u[:, 0, 1])
                        - (u[:, 2, 0] - u[:, 0, 0]) * (u[:, 1, 1] - u[:, 0, 1])) / 2
report['use_with_bag'] = round(float(area(UV1).sum()), 4)
report['bag_faces'] = int(len(bag_faces))
report['bag_density_ratio'] = round(float(np.sqrt(area(UV1[bag == 1]).sum() / area(UV0[bag == 1]).sum())), 4)
report['bag_rect'] = [round(float(x), 5) for x in (*UV1[bag == 1].reshape(-1, 2).min(0), *UV1[bag == 1].reshape(-1, 2).max(0))]
np.savez(os.path.join(HERE, 'work', 'uv_v3_bag.npz'), kind=bag[bag_faces], uv_old=UV0[bag_faces], uv_new=UV1[bag_faces],
         rel_faces=np.nonzero(rel)[0], rel_island=rel[rel > 0], rel_uv_new=UV1[rel > 0],
         rel_xyz=np.array([[me.vertices[v].co[:] for v in tri[f]] for f in np.nonzero(rel)[0]], np.float64))
json.dump(report, open(REPORT, 'w'), indent=1)
print('UV_REPORT', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = mesh.matrix_world
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('UV done; upload', UPLOAD, len(mesh.data.polygons))
