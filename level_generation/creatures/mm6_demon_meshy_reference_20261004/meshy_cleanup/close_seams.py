"""Close local shell backs and the annular clasp without capping its opening."""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

STAGE = Path(__file__).resolve().parent
geometry = json.loads((STAGE / 'repaired_geometry.json').read_text())
vertices = np.array(geometry['vertices_gltf'])
faces = np.array(geometry['faces'])
edge_faces = defaultdict(list)
for face_index, face in enumerate(faces):
    for a, b in zip(face, np.roll(face, -1)):
        edge_faces[tuple(sorted((int(a), int(b))))].append(face_index)
boundary_neighbors = defaultdict(list)
for (a, b), items in edge_faces.items():
    if len(items) == 1:
        boundary_neighbors[a].append(b)
        boundary_neighbors[b].append(a)
assert all(len(items) == 2 for items in boundary_neighbors.values())
loops = []
remaining = set(boundary_neighbors)
while remaining:
    first = min(remaining)
    loop = [first]
    previous = None
    current = first
    while True:
        following = next(value for value in boundary_neighbors[current] if value != previous)
        if following == first:
            break
        loop.append(following)
        previous, current = current, following
    remaining -= set(loop)
    loops.append(loop)
loops.sort(key=len, reverse=True)
assert [len(loop) for loop in loops] == [120, 20, 18, 16, 13, 11, 5, 5, 4]

def close_local_rim(loop):
    """Minimum-area 3D triangulation, favoring short edges on folded strap backs."""
    global vertices
    count = len(loop)
    positions = vertices[loop]
    distance_squared = np.sum((positions[:, None] - positions[None, :]) ** 2, axis=2)
    costs = np.full((count, count), np.inf)
    split = np.full((count, count), -1, dtype=int)
    for i in range(count - 1):
        costs[i, i + 1] = 0
    for span in range(2, count):
        for i in range(count - span):
            j = i + span
            diagonal = tuple(sorted((loop[i], loop[j])))
            if diagonal in edge_faces and len(edge_faces[diagonal]) != 1:
                continue
            candidates = np.arange(i + 1, j)
            cross = np.cross(positions[candidates] - positions[i], positions[j] - positions[i])
            areas = .5 * np.linalg.norm(cross, axis=1)
            shape_cost = .02 * (distance_squared[i, candidates] +
                                distance_squared[candidates, j] + distance_squared[i, j])
            options = costs[i, candidates] + costs[candidates, j] + areas + shape_cost
            options[areas < 1e-12] = np.inf
            best = int(np.argmin(options))
            costs[i, j] = options[best]
            split[i, j] = candidates[best]
    if not np.isfinite(costs[0, count - 1]):
        # A small nonplanar rim can have all candidate diagonals already occupied.
        # A local center closes it without creating overused existing edges.
        assert count <= 5, count
        center = positions.mean(axis=0)
        center_id = len(vertices)
        vertices = np.concatenate([vertices, center[None, :]])
        return [[a, b, center_id] for a, b in zip(loop, loop[1:] + loop[:1])]
    result = []
    stack = [(0, count - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        middle = int(split[i, j])
        result.append([loop[i], loop[middle], loop[j]])
        stack.extend([(i, middle), (middle, j)])
    return result

added = []
patch_reports = []
for loop in loops:
    if len(loop) in (20, 18):
        continue
    patch = close_local_rim(loop)
    added.extend(patch)
    patch_vertices = vertices[np.array(patch)]
    max_edge = max(float(np.linalg.norm(patch_vertices[:, i] - patch_vertices[:, j], axis=1).max())
                   for i, j in ((0, 1), (1, 2), (2, 0)))
    patch_reports.append({'boundary_vertices': len(loop), 'triangles': len(patch),
                          'max_new_edge': max_edge})
    assert max_edge < .055, patch_reports[-1]

# The clasp has two open rear rims. Join them as an annulus, keeping its center open.
outer = next(loop for loop in loops if len(loop) == 20)
inner_raw = next(loop for loop in loops if len(loop) == 18)
outer_position = vertices[outer]
best = None
for direction in (1, -1):
    candidate_base = inner_raw[::direction]
    for shift in range(len(candidate_base)):
        inner = candidate_base[shift:] + candidate_base[:shift]
        n, m = len(outer), len(inner)
        outer_closed = outer + [outer[0]]
        inner_closed = inner + [inner[0]]
        costs = np.full((n + 1, m + 1), np.inf)
        moves = np.zeros((n + 1, m + 1), dtype=int)
        costs[0, 0] = 0
        for i in range(n + 1):
            for j in range(m + 1):
                if i == j == 0:
                    continue
                edge_cost = float(np.sum((vertices[outer_closed[i]] - vertices[inner_closed[j]]) ** 2))
                a = costs[i - 1, j] if i else np.inf
                b = costs[i, j - 1] if j else np.inf
                if a < b:
                    costs[i, j] = a + edge_cost
                    moves[i, j] = 1
                else:
                    costs[i, j] = b + edge_cost
                    moves[i, j] = 2
        if best is None or costs[n, m] < best[0]:
            best = (costs[n, m], outer_closed, inner_closed, moves.copy())
_, outer_closed, inner_closed, moves = best
i, j = len(outer), len(inner_raw)
annulus = []
while i or j:
    if moves[i, j] == 1:
        annulus.append([outer_closed[i - 1], outer_closed[i], inner_closed[j]])
        i -= 1
    else:
        annulus.append([outer_closed[i], inner_closed[j], inner_closed[j - 1]])
        j -= 1
added.extend(annulus)
patch_reports.append({'boundary_vertices': [20, 18], 'triangles': len(annulus),
                      'repair': 'annular backing, center opening preserved'})
faces = np.concatenate([faces, np.array(added)])
# Coincident shell corners may share a coordinate but have disconnected face fans.
# Keep each closed fan as its own vertex rather than leaving bow-tie junctions.
vertex_faces = defaultdict(set)
all_edge_faces = defaultdict(set)
fan_faces = faces.copy()
for face_id, face in enumerate(faces):
    for vertex in face:
        vertex_faces[int(vertex)].add(face_id)
    for a, b in zip(face, np.roll(face, -1)):
        all_edge_faces[tuple(sorted((int(a), int(b))))].add(face_id)
split_fans = []
for vertex, incident in vertex_faces.items():
    remaining = incident.copy()
    groups = []
    while remaining:
        group = set()
        queue = [min(remaining)]
        while queue:
            face_id = queue.pop()
            if face_id in group:
                continue
            group.add(face_id)
            for other in fan_faces[face_id]:
                if other != vertex:
                    queue.extend(all_edge_faces[tuple(sorted((vertex, int(other))))] - group)
        groups.append(group)
        remaining -= group
    for group in groups[1:]:
        new_vertex = len(vertices)
        vertices = np.concatenate([vertices, vertices[vertex][None, :]])
        for face_id in group:
            faces[face_id, faces[face_id] == vertex] = new_vertex
        split_fans.append({'original_vertex': vertex, 'new_vertex': new_vertex,
                           'triangles': len(group)})
edges, multiplicities = np.unique(np.sort(np.concatenate([
    faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]
]), axis=1), axis=0, return_counts=True)
assert np.all(multiplicities == 2), np.unique(multiplicities, return_counts=True)
areas = .5 * np.linalg.norm(np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]],
                                    vertices[faces[:, 2]] - vertices[faces[:, 0]]), axis=1)
assert areas.min() > 1e-12
report = {'added_triangles': len(added), 'patches': patch_reports,
          'split_disconnected_vertex_fans': split_fans,
          'vertices': len(vertices), 'triangles': len(faces),
          'boundary_edges': 0, 'overused_edges': 0,
          'zero_area_faces': int((areas < 1e-12).sum()),
          'minimum_triangle_area': float(areas.min())}
(STAGE / 'closed_geometry.json').write_text(json.dumps({
    'vertices_gltf': vertices.tolist(), 'faces': faces.tolist()
}) + '\n')
(STAGE / 'seam_repair_audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
