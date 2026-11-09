"""Anatomical UV seams: a connected torso, separate head/ears, limbs, palms and finger charts."""
from collections import Counter, defaultdict
import heapq
import json

import bpy
from mathutils import Vector

from mesh_tools import ROOT


def unwrap():
    obj = bpy.data.objects['GB15 Skin body']
    mesh = obj.data
    marks = json.loads((ROOT / 'authoring/landmarks.json').read_text())

    def vertex_region(v):
        group = max(v.groups, key=lambda entry: entry.weight).group
        name = obj.vertex_groups[group].name
        if name.startswith(('digit.', 'thumb.')):
            return name.rsplit('.', 1)[0]
        if name.startswith(('forearm', 'upper_arm')):
            return 'arm' + name[-2:]
        if name.startswith(('thigh', 'shin')):
            return 'leg' + name[-2:]
        if name.startswith(('hand', 'foot')):
            return name
        if name == 'head':
            return ('ear.L' if v.co.x > 0 else 'ear.R') if abs(v.co.x) > .098 else 'head'
        return 'torso'

    regions = [vertex_region(v) for v in mesh.vertices]
    faces = {}
    edge_faces = defaultdict(list)
    region_faces = defaultdict(list)
    for p in mesh.polygons:
        label = Counter(regions[i] for i in p.vertices).most_common(1)[0][0]
        if label.startswith('foot'):
            label += '.sole' if p.normal.z < -.12 else '.top'
        faces[p.index] = label
        region_faces[label].append(p)
        for key in p.edge_keys:
            edge_faces[tuple(sorted(key))].append(p.index)
    edge_by_key = {tuple(sorted(edge.vertices)): edge for edge in mesh.edges}
    for edge in mesh.edges:
        linked = edge_faces[tuple(sorted(edge.vertices))]
        edge.use_seam = len(linked) != 2 or len({faces[i] for i in linked}) > 1
    for label, polys in region_faces.items():
        vertices = set(i for p in polys for i in p.vertices)
        if label.startswith('foot'):
            continue  # Sole/dorsum boundary already opens the branched toe surface.
        preferred = Vector((0, 1, 0))
        if label == 'torso':
            a, b = Vector((0, .046, .78)), Vector((0, .030, 1.43))
        elif label == 'head':
            a, b = Vector((0, .04, 1.43)), Vector((0, .04, 1.70))
        elif label.startswith('ear'):
            side = 1 if label.endswith('L') else -1
            a, b = Vector((side * .10, .04, 1.57)), Vector((side * .16, .06, 1.68))
        elif label.startswith(('digit', 'thumb')):
            a, b = Vector(marks[label][0]), Vector(marks[label][-1])
            preferred = Vector((0, -1, 0))
        else:
            suffix = label[-2:]
            keys = ('shoulder', 'wrist') if label.startswith('arm') else \
                ('hip', 'ankle') if label.startswith('leg') else ('wrist', 'hand_end')
            a, b = (Vector(marks[k + suffix]) for k in keys)
        axis = (b - a).normalized()
        axial = {i: (mesh.vertices[i].co - a).dot(axis) for i in vertices}
        low, high = min(axial.values()), max(axial.values())

        def side_cost(i):
            p = mesh.vertices[i].co - a
            radial = p - axis * p.dot(axis)
            return 1 - radial.normalized().dot(preferred) if radial.length > 1e-7 else 1

        start_candidates = [i for i in vertices if axial[i] < low + (high - low) * .08]
        end_candidates = [i for i in vertices if axial[i] > high - (high - low) * .04]
        start = min(start_candidates, key=side_cost)
        end = min(end_candidates, key=side_cost)
        adjacency = defaultdict(list)
        for p in polys:
            for key in p.edge_keys:
                i, j = key
                weight = (mesh.vertices[i].co - mesh.vertices[j].co).length * \
                    (1 + 8 * (side_cost(i) + side_cost(j)))
                adjacency[i].append((j, weight))
                adjacency[j].append((i, weight))
        queue, distances, previous = [(0, start)], {start: 0}, {}
        while queue:
            distance, i = heapq.heappop(queue)
            if i == end:
                break
            if distance > distances[i] + 1e-9:
                continue
            for j, weight in adjacency[i]:
                value = distance + weight
                if value < distances.get(j, float('inf')):
                    distances[j], previous[j] = value, i
                    heapq.heappush(queue, (value, j))
        current = end
        while current in previous:
            before = previous[current]
            edge_by_key[tuple(sorted((current, before)))].use_seam = True
            current = before
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='MINIMUM_STRETCH', no_flip=True, fill_holes=True, iterations=40, margin=.002)
    bpy.ops.object.mode_set(mode='OBJECT')
    print('Anatomical UV regions', len(region_faces), 'marked seams', sum(e.use_seam for e in mesh.edges))
