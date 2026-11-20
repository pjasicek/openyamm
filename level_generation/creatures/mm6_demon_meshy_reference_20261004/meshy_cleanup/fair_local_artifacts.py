"""Fair two reviewed pinch artifacts, leaving all other coordinates fixed."""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

stage = Path(__file__).resolve().parent
geometry = json.loads((stage / 'closed_geometry.json').read_text())
vertices = np.array(geometry['vertices_gltf'])
original = vertices.copy()
faces = np.array(geometry['faces'])
neighbors = defaultdict(set)
for face in faces:
    for a, b in zip(face, np.roll(face, -1)):
        neighbors[int(a)].add(int(b))
        neighbors[int(b)].add(int(a))
regions = [
    {'name': 'left_foot_toe_base_pinched_patch', 'center': [-.135, -.463, .199], 'radius': .027},
    {'name': 'left_inner_shin_fold', 'center': [-.12, -.332, .069], 'radius': .03},
]
weight = np.zeros(len(vertices))
for region in regions:
    distance = np.linalg.norm(original - region['center'], axis=1)
    blend = np.clip((1 - distance / region['radius']) * 2, 0, 1)
    weight = np.maximum(weight, blend)
    region['vertices_in_region'] = int((blend > 0).sum())
selected = np.flatnonzero(weight)
for iteration in range(6):
    previous = vertices.copy()
    for vertex in selected:
        mean = previous[sorted(neighbors[int(vertex)])].mean(axis=0)
        vertices[vertex] += .65 * weight[vertex] * (mean - previous[vertex])
areas = .5 * np.linalg.norm(np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]],
                                    vertices[faces[:, 2]] - vertices[faces[:, 0]]), axis=1)
assert areas.min() > 1e-12
movement = np.linalg.norm(vertices - original, axis=1)
report = {'regions': regions, 'iterations': 6,
          'moved_vertices': int((movement > 1e-12).sum()),
          'maximum_displacement_at_model_height_1': float(movement.max()),
          'all_other_vertex_coordinates_unchanged': bool(np.all(vertices[weight == 0] == original[weight == 0])),
          'zero_area_faces': int((areas < 1e-12).sum())}
(stage / 'final_geometry.json').write_text(json.dumps({
    'vertices_gltf': vertices.tolist(), 'faces': faces.tolist()
}) + '\n')
(stage / 'local_fairing_audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
