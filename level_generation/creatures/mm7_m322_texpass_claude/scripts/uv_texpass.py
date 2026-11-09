"""Texture-pass UVs for the installed m322 elf LOD0 (claude_shared/TEXTURE_QUALITY_PASS.md), run in Blender.

Builds the welded LOD0 surface from work/lod0_before.npz (same triangles, same order), lays one 2048 atlas with
claude_shared/uv_atlas.py (xatlas charts, small charts merged and re-flattened, one density, the approved head set's
skin, eyes and mouth (face, ears, scalp, neck top) x HEAD_FACTOR denser, the hair shell x HAIR_FACTOR and the hands
x HAND_FACTOR, 2 px margin)
and writes:
- work/uv_texpass.npz: per-triangle corner UVs (glTF convention, v down) in the GLB's triangle order;
- work/uv_texpass_report.json;
- texturing/<out>_body_upload.glb (whole body) and texturing/<out>_head_upload.glb (head-set faces only), static,
  no materials, smooth normals, on the new UVs, for the two Meshy retextures (enable_original_uv).

Never re-run once an upload went to Meshy: xatlas packs differently per run and the paid paint belongs to the layout.
Args: out=<name, default uv_texpass> [key=value uv_atlas.unwrap options]; never overwrites an existing layout
"""
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'claude_shared'))
import uv_atlas  # noqa: E402

HEAD_FACTOR = 1.8
HAIR_FACTOR = 1.25
HAND_FACTOR = 1.3
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
options = {k: (float(v) if '.' in v else int(v) if v.isdigit() else v) for k, v in (a.split('=', 1) for a in argv)}
out_npz = os.path.join(HERE, 'work', options.pop('out', 'uv_texpass') + '.npz')
if os.path.exists(out_npz):
    raise SystemExit(f'{out_npz} exists: a paint may belong to it; choose another out= name')

d = np.load(os.path.join(HERE, 'work', 'lod0_before.npz'))
pos, tri, weld, head_face, piece = d['pos'], d['tri'], d['weld'], d['head_face'], d['piece']
joints, weights, names = d['joints'], d['weights'], [str(n) for n in d['joint_names']]
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
for p in me.polygons:   # from_pydata keeps the order; check the vertices too
    assert tuple(p.vertices) == tuple(wtri[p.index])
obj = bpy.data.objects.new('Body', me)
bpy.context.scene.collection.objects.link(obj)

# head set weight: share of a vertex's faces that belong to the approved head set
count = np.bincount(wtri.ravel(), minlength=nweld).astype(float)
face_set = head_face & (piece != 1)
head_w = np.bincount(wtri[face_set].ravel(), minlength=nweld).astype(float) / np.maximum(count, 1)
hair_w = np.bincount(wtri[piece == 1].ravel(), minlength=nweld).astype(float) / np.maximum(count, 1)
hand_bones = [i for i, n in enumerate(names) if 'Hand' in n or 'Finger' in n]
hand_w_raw = np.zeros(len(pos))
for k in range(4):
    hand_w_raw += np.where(np.isin(joints[:, k], hand_bones), weights[:, k], 0)
hand_w = np.zeros(nweld)
hand_w[weld] = hand_w_raw
for name, w in (('HeadSet', head_w), ('Hair', hair_w), ('Hands', hand_w)):
    g = obj.vertex_groups.new(name=name)
    for v in np.nonzero(w > 0)[0]:
        g.add([int(v)], float(w[v]), 'REPLACE')

report = uv_atlas.unwrap(obj, head_groups=('HeadSet',), head_factor=HEAD_FACTOR, group_factors={'Hands': HAND_FACTOR, 'Hair': HAIR_FACTOR},
                         **options)
flat = np.zeros(len(me.loops) * 2, np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', flat)
flat = flat.reshape(-1, 2)
uv = np.array([flat[list(p.loop_indices)] for p in me.polygons], np.float64)
gl = uv.copy()
gl[..., 1] = 1 - gl[..., 1]                                      # Blender v up -> glTF v down
report['head_factor'] = HEAD_FACTOR
report['hand_factor'] = HAND_FACTOR
report['hair_factor'] = HAIR_FACTOR
report['faces'] = len(tri)
np.savez(out_npz, uv=gl, tri=tri, xyz=pos[tri])
json.dump(report, open(out_npz.replace('.npz', '_report.json'), 'w'), indent=1)
print('UV_TEXPASS', json.dumps(report))

os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
stem = os.path.basename(out_npz)[:-4]
for name, faces in ((stem + '_body_upload', np.ones(len(tri), bool)), (stem + '_head_upload', head_face)):
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
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', name + '.glb'), use_selection=True,
                              export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                              export_materials='NONE', export_attributes=False)
    print('UPLOAD', name, len(sub.polygons))
