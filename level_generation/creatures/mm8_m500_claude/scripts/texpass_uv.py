"""Texture pass step 2 (Blender): claude_shared/uv_atlas.py on the welded LOD0 (texpass_uv_prep.py).

Head-set charts 2.5x denser (the head set is 8 % of the surface; 2.5x gives body about 2.1x and head about 1.6x the
installed linear density at 55 % use of one 2048 square), 2 px margin. Writes the per-corner UVs in the installed
triangle order (texpass/uv_layout.npz), the report and the two neutral static uploads (whole body; head-set faces
alone with the same UVs) in the installed glTF frame. Never re-run once an upload went to Meshy.

Args: <uv_input.npz> <uv_layout.npz> <report.json> <body upload glb> <head upload glb> [key=value unwrap options]
"""
import json
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
import uv_atlas  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REPORT, BODY_UPLOAD, HEAD_UPLOAD = argv[:5]
options = {'head_factor': 2.5}
for item in argv[5:]:
    key, value = item.split('=', 1)
    options[key] = float(value) if '.' in value else int(value) if value.isdigit() else value

data = np.load(IN)
positions, faces, head_face, head_vertex = data['positions'], data['faces'], data['head_face'], data['head_vertex']
bpy.ops.wm.read_factory_settings(use_empty=True)
# glTF (x, y, z) -> Blender (x, -z, y), the importer's convention; uv_atlas works on lengths only.
blender_positions = np.stack([positions[:, 0], -positions[:, 2], positions[:, 1]], 1)
me = bpy.data.meshes.new('Body')
me.from_pydata(blender_positions.tolist(), [], faces.tolist())
me.update()
obj = bpy.data.objects.new('Body', me)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
group = obj.vertex_groups.new(name='HeadSet')
group.add([int(i) for i in np.nonzero(head_vertex)[0]], 1.0, 'REPLACE')
if len(me.polygons) != len(faces) or any(tuple(p.vertices) != tuple(f) for p, f in zip(me.polygons, faces)):
    raise RuntimeError('Blender changed the face order or corners')
head_factor = options.pop('head_factor')
report = uv_atlas.unwrap(obj, head_groups=('HeadSet',), head_factor=head_factor, **options)
corner_uv = np.zeros((len(faces), 3, 2))
layer = me.uv_layers['UVMap'].data
for p in me.polygons:
    for k, loop in enumerate(p.loop_indices):
        corner_uv[p.index, k] = layer[loop].uv
np.savez(OUT, corner_uv=corner_uv, head_face=head_face)
print('UV_ATLAS', json.dumps(report))
json.dump(report, open(REPORT, 'w'), indent=1)


def write_upload(path, selected):
    """Static neutral GLB: one primitive, positions in the installed glTF frame, per-corner UVs (glTF v down)."""
    import struct
    tri = np.nonzero(selected)[0]
    p = positions[faces[tri]].reshape(-1, 3).astype(np.float32)
    uv = corner_uv[tri].reshape(-1, 2).astype(np.float32).copy()
    uv[:, 1] = 1.0 - uv[:, 1]
    keys = {}
    vp, vt, idx = [], [], []
    for a, b in zip(p, uv):
        key = (tuple(np.round(a, 6)), tuple(np.round(b, 7)))
        if key not in keys:
            keys[key] = len(vp)
            vp.append(a)
            vt.append(b)
        idx.append(keys[key])
    vp, vt = np.array(vp, np.float32), np.array(vt, np.float32)
    idx = np.array(idx, np.uint32)
    blobs = [vp.tobytes(), vt.tobytes(), idx.tobytes()]
    views, offset = [], 0
    for blob in blobs:
        views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(blob)})
        offset += len(blob) + (-len(blob) % 4)
    binary = b''.join(blob + b'\0' * (-len(blob) % 4) for blob in blobs)
    doc = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': [0]}],
           'nodes': [{'mesh': 0, 'name': 'WaterElemental_body'}],
           'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'TEXCOORD_0': 1}, 'indices': 2}]}],
           'accessors': [
               {'bufferView': 0, 'componentType': 5126, 'count': len(vp), 'type': 'VEC3',
                'min': vp.min(0).tolist(), 'max': vp.max(0).tolist()},
               {'bufferView': 1, 'componentType': 5126, 'count': len(vt), 'type': 'VEC2'},
               {'bufferView': 2, 'componentType': 5125, 'count': len(idx), 'type': 'SCALAR'}],
           'bufferViews': views, 'buffers': [{'byteLength': len(binary)}]}
    text = json.dumps(doc).encode()
    text += b' ' * (-len(text) % 4)
    with open(path, 'wb') as out:
        out.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(text) + 8 + len(binary)))
        out.write(struct.pack('<II', len(text), 0x4E4F534A) + text)
        out.write(struct.pack('<II', len(binary), 0x004E4942) + binary)
    print('UPLOAD', path, len(tri), 'triangles', len(vp), 'vertices')


os.makedirs(os.path.dirname(BODY_UPLOAD), exist_ok=True)
write_upload(BODY_UPLOAD, np.ones(len(faces), bool))
write_upload(HEAD_UPLOAD, head_face)
