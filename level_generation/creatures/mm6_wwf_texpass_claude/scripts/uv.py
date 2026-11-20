"""Texture-pass UVs (Blender) on the welded layout meshes of work/lod0_before.npz, with claude_shared/uv_atlas.py:
one 2048 atlas, head_bones x head_factor denser, group_factors per bone group, 2 px margin. Writes
- work/<out>.npz: corner UVs (T,3,2, glTF v down) in the dump's triangle order, tri, xyz, part;
- work/<out>_report.json;
- texturing/<out>_body_upload.glb (all faces) and, with head_upload, texturing/<out>_head_upload.glb (faces whose
  corners are mostly head-weighted): static, no materials, smooth normals, glTF frame = the GLB's bind pose.
Never re-run once an upload went to Meshy (xatlas packs differently per run). Refuses to overwrite a layout.
Args after --: out=<name> [uv_atlas.unwrap key=value options]"""
import json
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tp  # noqa: E402
import uv_atlas  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def value(v):
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


options = {k: value(v) for k, v in (a.split('=', 1) for a in argv)}
out_npz = str(tp.HERE / 'work' / (options.pop('out', 'uv_texpass') + '.npz'))
if os.path.exists(out_npz):
    raise SystemExit(f'{out_npz} exists: a paint may belong to it; choose another out= name')

d = np.load(tp.HERE / 'work' / 'lod0_before.npz')
pos, tri, weld, head_w, part = d['pos'], d['tri'], d['weld'], d['head_w'], d['part']
nweld = int(weld.max()) + 1
wpos = np.zeros((nweld, 3))
wpos[weld] = pos
wtri = weld[tri]
blender = np.stack([wpos[:, 0], -wpos[:, 2], wpos[:, 1]], 1)     # glTF Y-up -> Blender Z-up

bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('Body')
me.from_pydata(blender.tolist(), [], wtri.tolist())
me.update()
assert len(me.polygons) == len(tri)
for p in me.polygons:
    assert tuple(p.vertices) == tuple(wtri[p.index])
obj = bpy.data.objects.new('Body', me)
bpy.context.scene.collection.objects.link(obj)


def weld_max(w):
    out = np.zeros(nweld)
    np.maximum.at(out, weld, w)
    return out


factors = {}
groups = [('HeadSet', weld_max(head_w))]
for k, name in enumerate(d['group_names']):
    groups.append((str(name), weld_max(d['group_w'][k])))
    factors[str(name)] = tp.CFG['group_factors'][str(name)][1]
for name, w in groups:
    g = obj.vertex_groups.new(name=name)
    for v in np.nonzero(w > 0)[0]:
        g.add([int(v)], float(w[v]), 'REPLACE')
# skin weights per joint (2026-11-12 defaults: PartUV's part tree is built from every vertex group's weights)
joints, weights = d['joints'], d['weights']
for j, jname in enumerate(d['joint_names']):
    w = weld_max(np.where(joints == j, weights, 0).sum(1))
    if (w > 0).any():
        g = obj.vertex_groups.new(name='J_' + str(jname))
        for v in np.nonzero(w > 0)[0]:
            g.add([int(v)], float(w[v]), 'REPLACE')

head_factor = tp.CFG.get('head_factor', 1.0)
report = uv_atlas.unwrap(obj, head_groups=('HeadSet',), head_factor=head_factor, group_factors=factors or None,
                         **options)
flat = np.zeros(len(me.loops) * 2, np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', flat)
flat = flat.reshape(-1, 2)
uv = np.array([flat[list(p.loop_indices)] for p in me.polygons], np.float64)
gl = uv.copy()
gl[..., 1] = 1 - gl[..., 1]                                      # Blender v up -> glTF v down
report.update(head_factor=head_factor, group_factors=factors, faces=len(tri), options=options)
np.savez(out_npz, uv=gl, tri=tri, xyz=pos[tri], part=part)
json.dump(report, open(out_npz.replace('.npz', '_report.json'), 'w'), indent=1, default=str)
print('UV_TEXPASS', json.dumps(report, default=str))

os.makedirs(tp.HERE / 'texturing', exist_ok=True)
stem = os.path.basename(out_npz)[:-4]
uploads = [(stem + '_body_upload', np.ones(len(tri), bool))]
if tp.CFG.get('head_upload'):
    uploads.append((stem + '_head_upload', head_w[tri].mean(1) > 0.5))
for name, faces in uploads:
    sub = bpy.data.meshes.new(name)
    keep = np.nonzero(faces)[0]
    verts = np.unique(wtri[keep])
    index = np.full(nweld, -1)
    index[verts] = np.arange(len(verts))
    sub.from_pydata(blender[verts].tolist(), [], index[wtri[keep]].tolist())
    sub.update()
    for p in sub.polygons:
        p.use_smooth = True
    layer = sub.uv_layers.new(name='UVMap')
    loops = np.zeros((len(sub.loops), 2), np.float32)
    for p in sub.polygons:
        loops[list(p.loop_indices)] = uv[keep[p.index]]
    layer.data.foreach_set('uv', loops.ravel())
    ob = bpy.data.objects.new(name, sub)
    bpy.context.scene.collection.objects.link(ob)
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=str(tp.HERE / 'texturing' / (name + '.glb')), use_selection=True,
                              export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                              export_materials='NONE', export_attributes=False)
    print('UPLOAD', name, len(sub.polygons))
