"""Locally reshape the selected head; preserve topology, UVs, weights, clips and every material variant."""
import copy
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

stage = Path(__file__).resolve().parent
source = stage.parent / 'variants_20261006'
sys.path.insert(0, str(stage.parents[3] / 'tools'))
from build_actor_lods import accessor_bytes, read_glb, write_glb


def smooth(value, low, high):
    t = np.clip((value - low) / (high - low), 0, 1)
    return t * t * (3 - 2 * t)


def deform(points):
    """Blender rest coordinates: Z up, negative Y towards the face. Eyeballs use a separate material."""
    p = np.array(points, dtype=np.float64)
    x, y, z = p.T
    dx = x + .006
    face = (1 - smooth(np.abs(dx), .062, .086)) * smooth(-y, .29, .34)
    face *= smooth(z, 1.45, 1.49)
    brow = np.exp(-((z - 1.634) / .025) ** 2) * face
    inner = 1 - smooth(np.abs(dx), .019, .061)
    # A heavier brow covers the upper iris instead of leaving two exposed circular eyes.
    p[:, 2] -= (.004 + .009 * inner) * brow
    p[:, 1] -= (.006 + .007 * inner) * brow
    # Flatten the raised central forehead while retaining the native ears and the skull silhouette.
    crest = face * smooth(z, 1.641, 1.67) * (1 - smooth(np.abs(dx), .025, .055))
    p[:, 2] -= .012 * crest
    # Give the mouth vertical depth and a squarer jaw. Upper muzzle and eye positions stay fixed.
    jaw = face * (1 - smooth(z, 1.532, 1.558))
    p[:, 2] -= .014 * jaw
    p[:, 0] += dx * .06 * jaw
    # Lower the raised corners that made the tooth display read as a smiling arc.
    corners = face * np.exp(-((np.abs(dx) - .052) / .020) ** 2 - ((z - 1.557) / .022) ** 2)
    p[:, 2] -= .009 * corners
    return p


def values(document, binary, index):
    a = document['accessors'][index]
    dtype = {5121: '<u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']]
    return np.frombuffer(accessor_bytes(document, binary, index), dtype).reshape(a['count'], -1).copy()


def replace(document, binary, index, array):
    a = document['accessors'][index]
    view = document['bufferViews'][a['bufferView']]
    offset = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = view.get('byteStride', array.shape[1] * 4)
    target = np.ndarray(array.shape, dtype='<f4', buffer=binary, offset=offset, strides=(stride, 4))
    target[:] = array


def sculpt_primitive(document, binary, primitive):
    attributes = primitive['attributes']
    old = values(document, binary, attributes['POSITION'])
    # glTF uses Y up and positive Z towards the face.
    rest = old[:, [0, 2, 1]] * [1, -1, 1]
    changed = deform(rest)
    mask = np.any(np.abs(changed - rest) > 1e-10, axis=1)
    new = (changed * [1, -1, 1])[:, [0, 2, 1]].astype('<f4')
    normals = values(document, binary, attributes['NORMAL'])
    result = normals.copy()
    # Preserve authored seam/hard-edge normals using the sculpt's inverse-transpose Jacobian.
    epsilon = .00002
    jacobian = np.empty((mask.sum(), 3, 3))
    for axis in range(3):
        step = np.zeros(3)
        step[axis] = epsilon
        jacobian[:, :, axis] = (deform(rest[mask] + step) - deform(rest[mask] - step)) / (2 * epsilon)
    determinants = np.linalg.det(jacobian)
    assert np.all(determinants > .15), 'sculpt folded the head surface'
    transformed = np.linalg.solve(jacobian.transpose(0, 2, 1),
        (normals[mask][:, [0, 2, 1]] * [1, -1, 1])[..., None])[..., 0]
    transformed /= np.linalg.norm(transformed, axis=1)[:, None]
    result[mask] = (transformed * [1, -1, 1])[:, [0, 2, 1]]
    triangles = values(document, binary, primitive['indices']).ravel().reshape(-1, 3)
    previous_cross = np.cross(old[triangles[:, 1]] - old[triangles[:, 0]],
                              old[triangles[:, 2]] - old[triangles[:, 0]])
    new_cross = np.cross(new[triangles[:, 1]] - new[triangles[:, 0]],
                         new[triangles[:, 2]] - new[triangles[:, 0]])
    touched = mask[triangles].any(1)
    assert np.all(np.sum(previous_cross[touched] * new_cross[touched], axis=1) > 0), 'inverted triangle'
    replace(document, binary, attributes['POSITION'], new)
    replace(document, binary, attributes['NORMAL'], result)
    a = document['accessors'][attributes['POSITION']]
    a['min'], a['max'] = new.min(0).tolist(), new.max(0).tolist()
    return {'modified_vertices': int(mask.sum()), 'minimum_jacobian': float(determinants.min()),
            'maximum_displacement': float(np.linalg.norm(changed - rest, axis=1).max())}


def export(name):
    before, original = read_glb(source / name)
    document, binary = copy.deepcopy(before), bytearray(original)
    body = next(n['mesh'] for n in document['nodes'] if n.get('name') == 'Demon_Native_Mesh')
    mesh = document['meshes'][body]
    levels = [body] + mesh.get('extras', {}).get('openyamm_lods', [])
    shadows = mesh.get('extras', {}).get('openyamm_shadow_lods', [])
    assert not shadows or len(shadows) == len(levels)
    changed_accessors = set()
    report = []
    for level_index, level in enumerate(levels):
        primitives = document['meshes'][level]['primitives']
        skin = next(p for p in primitives if document['materials'][p['material']]['name'] == 'Demon_Meshy_Body')
        report.append(sculpt_primitive(document, binary, skin))
        changed_accessors.update(skin['attributes'][semantic] for semantic in ('POSITION', 'NORMAL'))
        if not shadows:
            continue
        shadow = shadows[level_index]
        # Shadow buffers contain the same color vertices concatenated, including unchanged eye/claw sections.
        for semantic in ('POSITION', 'NORMAL'):
            combined = np.concatenate([values(document, binary, p['attributes'][semantic]) for p in primitives])
            target = document['meshes'][shadow]['primitives'][0]['attributes'][semantic]
            changed_accessors.add(target)
            assert combined.shape == values(document, binary, target).shape
            replace(document, binary, target, combined)
            if semantic == 'POSITION':
                a = document['accessors'][target]
                a['min'], a['max'] = combined.min(0).tolist(), combined.max(0).tolist()
    assert len(binary) == len(original)
    for key in ('nodes', 'skins', 'animations', 'materials', 'images', 'textures', 'extensions'):
        assert before[key] == document[key], key
    assert before['meshes'] == document['meshes'], 'topology or LOD selection changed'
    for i in range(len(document['accessors'])):
        if i not in changed_accessors:
            a = document['accessors'][i]
            assert before['accessors'][i] == a, i
            if 'sparse' in a:
                # Portable death-plume morphs are sparse; retain their encoded index/value views verbatim.
                views = [a['sparse'][name]['bufferView'] for name in ('indices', 'values')]
                if 'bufferView' in a:
                    views.append(a['bufferView'])
                for index in views:
                    view = document['bufferViews'][index]
                    start = view.get('byteOffset', 0)
                    end = start + view['byteLength']
                    assert original[start:end] == binary[start:end], i
            else:
                assert accessor_bytes(before, original, i) == accessor_bytes(document, binary, i), i
    destination = stage / name
    write_glb(destination, document, bytes(binary))
    return {'source_sha256': hashlib.sha256((source / name).read_bytes()).hexdigest(),
            'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(), 'lods': report,
            'uv_weights_clips_rig_materials_unchanged': True, 'binary_size_unchanged': True}


if __name__ == '__main__':
    report = {name: export(name) for name in ('mm6_demon_runtime.glb', 'mm6_demon_animated.glb')}
    bpy.ops.wm.open_mainfile(filepath=str(source / 'mm6_demon_variants_master.blend'))
    body = bpy.data.objects['Demon_Native_Mesh']
    eye_vertices = {i for polygon in body.data.polygons if polygon.material_index in (1, 2)
                    for i in polygon.vertices}
    points = np.array([v.co[:] for v in body.data.vertices])
    revised = deform(points)
    revised[list(eye_vertices)] = points[list(eye_vertices)]
    for vertex, point in zip(body.data.vertices, revised):
        vertex.co = point
    body.data.update()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'mm6_demon_expression_master.blend'), compress=True)
    master_hash = hashlib.sha256((stage / 'mm6_demon_expression_master.blend').read_bytes()).hexdigest()
    report['master'] = {'sha256': master_hash,
                        'modified_vertices': int(np.any(revised != points, axis=1).sum())}
    (stage / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
