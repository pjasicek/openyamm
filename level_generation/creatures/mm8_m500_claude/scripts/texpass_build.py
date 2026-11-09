"""Texture pass step 6: the runtime GLB = the installed GLB with only UVs, images and ramps changed.

- LOD0 (and its identical full-detail shadow): each corner takes its new UV; vertices are split where UVs differ,
  every other attribute is copied from the installed vertex, triangle order kept.
- LOD1 and the other shadow LODs (sampling the shared atlas; their vertices moved in the reduction): each corner
  takes the UV of its closest facing LOD0 point; a triangle across a chart seam keeps one chart (remap()).
- LOD2/LOD3 keep their own geometry and UVs from the far-LOD repair (lod_repair_claude); their images are
  transferred again from the new LOD0 maps with its transfer_textures.transfer (same sizes).
- The four shared images are replaced (2K colour and normal, 1K metal/roughness and mask) and every material's ramps
  come from textures/m500_tp_ramps.json by tier.
Usage: texpass_build.py <uv_layout.npz> <out.glb>
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texpass_glb import (BEFORE, PROJECT, TP, append_accessor, compact, floats, mesh_by_name, np,  # noqa: E402
                         read_glb, rows, source_faces, write_glb)
from scipy.spatial import cKDTree  # noqa: E402
from transfer_textures import closest_on_triangles, transfer  # noqa: E402

T = PROJECT / 'textures'
layout = np.load(sys.argv[1])
OUT = Path(sys.argv[2])
corner_uv = layout['corner_uv'].copy()
corner_uv[..., 1] = 1.0 - corner_uv[..., 1]  # glTF v
welded_faces = np.load(TP / 'uv_input.npz')['faces']
doc, binary = read_glb(BEFORE)
binary = bytearray(binary)
report = {}


def rebuild(primitive, per_corner_uv):
    """New vertices (installed vertex + UV per corner, deduplicated) and indices for one primitive."""
    faces = source_faces(doc, binary, primitive)
    keys, index_of, out_faces = [], {}, np.zeros_like(faces)
    for t, (tri, uvs) in enumerate(zip(faces, per_corner_uv)):
        for k in range(3):
            key = (int(tri[k]), round(float(uvs[k, 0]), 7), round(float(uvs[k, 1]), 7))
            if key not in index_of:
                index_of[key] = len(keys)
                keys.append(key)
            out_faces[t, k] = index_of[key]
    references = np.array([k[0] for k in keys])
    new_uv = np.array([k[1:] for k in keys], np.float32)
    attributes = {}
    for semantic, index in primitive['attributes'].items():
        accessor = copy.deepcopy(doc['accessors'][index])
        data = new_uv.view(np.uint8).reshape(len(keys), -1) if semantic == 'TEXCOORD_0' \
            else rows(doc, binary, index)[references]
        accessor['count'] = len(keys)
        accessor.pop('min', None)
        accessor.pop('max', None)
        if semantic == 'POSITION':
            values = data.copy().view(np.float32).reshape(-1, 3)
            accessor['min'], accessor['max'] = values.min(0).tolist(), values.max(0).tolist()
        attributes[semantic] = append_accessor(doc, binary, accessor, data.tobytes())
    index_type = 5123 if len(keys) < 65536 else 5125
    indices = append_accessor(doc, binary, {'componentType': index_type, 'type': 'SCALAR', 'count': out_faces.size},
                              out_faces.astype(np.uint16 if index_type == 5123 else np.uint32).tobytes())
    primitive['attributes'] = attributes
    primitive['indices'] = indices
    return len(keys)


# ---- LOD0 and its full-detail shadow
lod0 = doc['meshes'][mesh_by_name(doc, 'Body')]['primitives'][0]
p0 = floats(doc, binary, lod0['attributes']['POSITION'])
f0 = source_faces(doc, binary, lod0)
shadow = doc['meshes'][mesh_by_name(doc, 'Body_Shadow')]['primitives'][0]
assert (source_faces(doc, binary, shadow) == f0).all()
assert np.array_equal(floats(doc, binary, shadow['attributes']['POSITION']), p0)
report['lod0_vertices'] = [len(p0), rebuild(lod0, corner_uv)]
report['shadow_vertices'] = rebuild(shadow, corner_uv)

# ---- charts of the new layout: faces joined across an edge whose two corners keep their UVs
parent = np.arange(len(f0))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


edge_owner = {}
for f, tri in enumerate(welded_faces):
    for k in range(3):
        a, b = int(tri[k]), int(tri[(k + 1) % 3])
        key = (min(a, b), max(a, b))
        uv_of = {a: corner_uv[f, k], b: corner_uv[f, (k + 1) % 3]}
        if key in edge_owner:
            g, other = edge_owner[key]
            if all(np.abs(uv_of[v] - other[v]).max() < 1e-6 for v in key):
                parent[find(f)] = find(g)
        else:
            edge_owner[key] = (f, uv_of)
chart = np.array([find(f) for f in range(len(f0))])
report['charts'] = int(len(np.unique(chart)))
centroids = p0[f0].mean(1)
face_normal = np.cross(p0[f0[:, 1]] - p0[f0[:, 0]], p0[f0[:, 2]] - p0[f0[:, 0]])
face_normal /= np.maximum(np.linalg.norm(face_normal, axis=1, keepdims=True), 1e-12)
tree = cKDTree(centroids)
chart_faces = {c: np.nonzero(chart == c)[0] for c in np.unique(chart)}


def remap(primitive, name):
    """Per-corner UVs of a coarser mesh on the new LOD0 charts: each corner's closest facing LOD0 point; a triangle
    whose corners land on different charts keeps the chart its centroid and corners vote for (centroid twice) and
    extends that chart's nearest triangle's UV map linearly to the other corners."""
    positions = floats(doc, binary, primitive['attributes']['POSITION'])
    faces = source_faces(doc, binary, primitive)
    tri = positions[faces]
    normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)

    def nearest(points, normals):
        _, candidates = tree.query(points, k=32)
        a, b, c = (p0[f0[candidates, i]] for i in range(3))
        distance, bary = closest_on_triangles(points, a, b, c)
        cost = distance + np.where((face_normal[candidates] * normals[:, None]).sum(-1) < -.2, 1e3, 0)
        pick = np.argmin(cost, 1)
        rows = np.arange(len(points))
        return candidates[rows, pick], bary[rows, pick]

    corner_face, corner_bary = nearest(tri.reshape(-1, 3), np.repeat(normal, 3, 0))
    corner_face, corner_bary = corner_face.reshape(-1, 3), corner_bary.reshape(-1, 3, 3)
    centre_face, _ = nearest(tri.mean(1), normal)
    out = np.zeros((len(faces), 3, 2))
    extended = 0
    for t in range(len(faces)):
        votes = [chart[centre_face[t]], chart[centre_face[t]]] + [chart[f] for f in corner_face[t]]
        owner = max(set(votes), key=votes.count)
        pool = chart_faces[owner]
        for k in range(3):
            f = corner_face[t, k]
            if chart[f] == owner:
                out[t, k] = (corner_bary[t, k][:, None] * corner_uv[f]).sum(0)
                continue
            extended += 1
            # Linear extension of the owner chart's nearest triangle (build_lods.extend_uv's method).
            g = pool[np.argmin(np.linalg.norm(centroids[pool] - tri[t, k], axis=1))]
            a, b, c = p0[f0[g]]
            e1, e2, d = b - a, c - a, tri[t, k] - a
            m = np.array([[e1 @ e1, e1 @ e2], [e1 @ e2, e2 @ e2]])
            v, w = np.linalg.solve(m + np.eye(2) * 1e-18, np.array([d @ e1, d @ e2]))
            out[t, k] = corner_uv[g, 0] * (1 - v - w) + corner_uv[g, 1] * v + corner_uv[g, 2] * w
    report[name] = {'triangles': int(len(faces)), 'corners_extended': int(extended)}
    rebuild(primitive, out)
    return out


for name in ('Body_LOD1', 'Body_LOD1_Shadow', 'Body_LOD2_Shadow', 'Body_LOD3_Shadow'):
    remap(doc['meshes'][mesh_by_name(doc, name)]['primitives'][0], name)


# ---- images
def set_image(index, path, name):
    data = Path(path).read_bytes()
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary.extend(data)
    doc['images'][index].update(bufferView=len(doc['bufferViews']) - 1, name=name, mimeType='image/png')


material = doc['materials'][0]
image_of = lambda texture: doc['textures'][texture['index']]['source']  # noqa: E731
set_image(image_of(material['pbrMetallicRoughness']['baseColorTexture']), T / 'm500_tp_basecolor_2k.png',
          'm500_tp_basecolor_2k')
set_image(image_of(material['pbrMetallicRoughness']['metallicRoughnessTexture']), T / 'm500_tp_metal_rough_1k.png',
          'm500_tp_metal_rough_1k')
set_image(image_of(material['normalTexture']), T / 'm500_tp_normal_2k.png', 'm500_tp_normal_2k')
set_image(image_of(material['extras']['openyamm_region_mask']), T / 'm500_tp_region_mask_1k.png',
          'm500_tp_region_mask_1k')

# ---- far LODs: same geometry and UVs, maps transferred again from the new LOD0
far_dir = TP / 'far'
far_dir.mkdir(exist_ok=True)
for level in (2, 3):
    primitive = doc['meshes'][mesh_by_name(doc, f'Body_LOD{level}')]['primitives'][0]
    lod_material = doc['materials'][primitive['material']]
    corners = source_faces(doc, binary, primitive)
    lod_uv = floats(doc, binary, primitive['attributes']['TEXCOORD_0'])[corners]
    slots = {'basecolor': lod_material['pbrMetallicRoughness']['baseColorTexture'],
             'mr': lod_material['pbrMetallicRoughness']['metallicRoughnessTexture'],
             'normal': lod_material['normalTexture'], 'mask': lod_material['extras']['openyamm_region_mask']}
    first = doc['images'][image_of(slots['basecolor'])]
    view = doc['bufferViews'][first['bufferView']]
    from PIL import Image
    import io
    size = Image.open(io.BytesIO(binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']])).size[0]
    maps, coverage = transfer(doc, bytes(binary), lod0, primitive, corners, lod_uv, size)
    for kind, picture in maps.items():
        path = far_dir / f'lod{level}_{kind}.png'
        picture.save(path)
        index = image_of(slots[kind])
        set_image(index, path, doc['images'][index]['name'])
    report[f'lod{level}_transfer'] = {'size': size, 'coverage': round(float(coverage), 3)}

# ---- ramps by tier
ramps = json.loads((T / 'm500_tp_ramps.json').read_text())['materials'][0]['ramps']
for m in doc['materials']:
    tier = m['name'].split('_')[1].lower()
    m['extras']['openyamm_region_ramps'] = ramps[f'water_{tier}']
packed = compact(doc, binary)
OUT.parent.mkdir(parents=True, exist_ok=True)
write_glb(OUT, doc, bytes(packed))
report['bytes'] = OUT.stat().st_size
(TP / 'build_report.json').write_text(json.dumps(report, indent=1) + '\n')
print(json.dumps(report, indent=1))
