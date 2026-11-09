"""Local cap repair for this supplied Meshy asset; no whole-body smoothing."""
import hashlib
import json
import struct
from collections import defaultdict
from pathlib import Path

import numpy as np

STAGE = Path(__file__).resolve().parent
SOURCE = Path('/home/pjasicek/Downloads/Meshy_AI_Spineclaw_Warlord_1004160609_generate.glb')
data = SOURCE.read_bytes()
chunks = {}
offset = 12
while offset < len(data):
    length, kind = struct.unpack_from('<II', data, offset)
    offset += 8
    chunks[kind] = data[offset:offset + length]
    offset += length
document = json.loads(chunks[0x4E4F534A])
raw = chunks[0x004E4942]
vertices = np.frombuffer(raw, '<f4', count=7912 * 3).reshape((-1, 3)).astype(float)
faces = np.frombuffer(raw, '<u4', count=15487 * 3, offset=94944).reshape((-1, 3)).copy()
original = vertices.copy()
neighbors = defaultdict(set)
for face in faces:
    for a, b in zip(face, np.roll(face, -1)):
        neighbors[int(a)].add(int(b))
        neighbors[int(b)].add(int(a))

# Twenty independent caps erroneously share a single coordinate in the source.
bad_poles = np.flatnonzero(np.all(original == original[7890], axis=1)).tolist()
assert bad_poles == [7064] + list(range(7890, 7909)), bad_poles
# These ten tessellation helpers were interpolated using the displaced caps.
helpers = [7841, 7855, 7858, 7860, 7862, 7867, 7869, 7871, 7872, 7874]
# Isolated single triangles have no surrounding surface: they are artifacts.
orphan_poles = [7899, 7906, 7907]
removed_faces = np.flatnonzero(np.any(np.isin(faces, orphan_poles), axis=1)).tolist()
faces = faces[~np.any(np.isin(faces, orphan_poles), axis=1)]
unknown = sorted((set(bad_poles) | set(helpers)) - set(orphan_poles))
index = {value: row for row, value in enumerate(unknown)}
matrix = np.zeros((len(unknown), len(unknown)))
rhs = np.zeros((len(unknown), 3))
for vertex, row in index.items():
    adjacent = neighbors[vertex]
    matrix[row, row] = len(adjacent)
    for adjacent_vertex in adjacent:
        if adjacent_vertex in index:
            matrix[row, index[adjacent_vertex]] -= 1
        else:
            rhs[row] += original[adjacent_vertex]
vertices[unknown] = np.linalg.solve(matrix, rhs)

# Weld only exact coincident coordinates after the incorrect caps have moved.
unique, inverse = np.unique(vertices, axis=0, return_inverse=True)
faces = inverse[faces]
degenerate = np.array([len(set(face)) != 3 for face in faces])
faces = faces[~degenerate]
_, unique_face_indices = np.unique(np.sort(faces, axis=1), axis=0, return_index=True)
duplicate_faces_removed = len(faces) - len(unique_face_indices)
faces = faces[np.sort(unique_face_indices)]
used = np.unique(faces)
remap = np.full(len(unique), -1)
remap[used] = np.arange(len(used))
vertices_out = unique[used]
faces = remap[faces]

edge_faces = defaultdict(list)
for face_index, face in enumerate(faces):
    for a, b in zip(face, np.roll(face, -1)):
        edge_faces[tuple(sorted((int(a), int(b))))].append(face_index)
boundary = [edge for edge, items in edge_faces.items() if len(items) == 1]
overused = {str(edge): items for edge, items in edge_faces.items() if len(items) > 2}
boundary_neighbors = defaultdict(set)
for a, b in boundary:
    boundary_neighbors[a].add(b)
    boundary_neighbors[b].add(a)
groups = []
remaining = set(boundary_neighbors)
while remaining:
    group = set()
    queue = [min(remaining)]
    while queue:
        vertex = queue.pop()
        if vertex in group:
            continue
        group.add(vertex)
        queue.extend(boundary_neighbors[vertex] - group)
    remaining -= group
    groups.append({
        'vertices': sorted(group),
        'count': len(group),
        'degree': sorted({len(boundary_neighbors[value]) for value in group}),
        'center': vertices_out[sorted(group)].mean(axis=0).tolist(),
        'extent': np.ptp(vertices_out[sorted(group)], axis=0).tolist(),
    })
edges = np.array(list(edge_faces))
lengths = np.linalg.norm(vertices_out[edges[:, 0]] - vertices_out[edges[:, 1]], axis=1)
report = {
    'source': str(SOURCE),
    'source_sha256': hashlib.sha256(data).hexdigest(),
    'repaired_cap_vertices': bad_poles,
    'repaired_interpolation_vertices': helpers,
    'removed_orphan_faces': removed_faces,
    'duplicate_faces_removed': duplicate_faces_removed,
    'degenerate_faces_removed': int(degenerate.sum()),
    'vertices': len(vertices_out),
    'faces': len(faces),
    'boundary_edges': len(boundary),
    'overused_edges': overused,
    'max_edge': float(lengths.max()),
    'long_edges_over_0_06': int((lengths > .06).sum()),
    'boundary_groups': sorted(groups, key=lambda item: -item['count']),
    'local_moves': {str(i): {'old': original[i].tolist(), 'new': vertices[i].tolist()}
                    for i in unknown},
}
(STAGE / 'local_repair_audit.json').write_text(json.dumps(report, indent=2) + '\n')
(STAGE / 'repaired_geometry.json').write_text(json.dumps({
    'vertices_gltf': vertices_out.tolist(), 'faces': faces.tolist()
}) + '\n')
print(json.dumps({key: value for key, value in report.items()
                  if key not in ('local_moves', 'boundary_groups')}, indent=2))
print('Boundary groups:', [(group['count'], group['degree'],
                            [round(v, 4) for v in group['center']],
                            [round(v, 4) for v in group['extent']])
                           for group in report['boundary_groups']])
