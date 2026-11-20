"""Small explicit topology tools shared by this character's authoring stages."""
from pathlib import Path
import math
import json

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]


def mix(a, b, t):
    return a * (1 - t) + b * t


def curve(points, x):
    if x <= points[0][0]:
        return points[0][1]
    for (a, va), (b, vb) in zip(points, points[1:]):
        if x <= b:
            return mix(va, vb, (x - a) / (b - a))
    return points[-1][1]


def blend_weights(a, b, t):
    result = {name: value * (1 - t) for name, value in a.items()}
    for name, value in b.items():
        result[name] = result.get(name, 0) + value * t
    return {name: value for name, value in result.items() if value > 1e-6}


def material(name, color, roughness=.6, metal=0):
    mat = bpy.data.materials.get('GB15 ' + name) or bpy.data.materials.new('GB15 ' + name)
    mat.use_nodes = True
    shader = next(node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metal
    mat.diffuse_color = (*color, 1)
    return mat


class Mesh:
    def __init__(self, name, mat):
        self.name, self.mat = name, mat
        self.vertices, self.faces, self.weights = [], [], []

    def vertex(self, point, weights=None):
        self.vertices.append(Vector(point))
        self.weights.append(dict(weights or {}))
        return len(self.vertices) - 1

    def face(self, vertices):
        if len(set(vertices)) >= 3:
            self.faces.append(tuple(vertices))

    def bridge(self, a, b, align=False):
        original = b
        if align:
            b = self.align(a, b)
        i, j, na, nb = 0, 0, len(a), len(b)
        while i < na or j < nb:
            next_a, next_b = (i + 1) / na, (j + 1) / nb
            if abs(next_a - next_b) < 1e-7:
                self.face((a[i % na], a[(i + 1) % na], b[(j + 1) % nb], b[j % nb]))
                i, j = i + 1, j + 1
            elif next_a < next_b:
                self.face((a[i % na], a[(i + 1) % na], b[j % nb]))
                i += 1
            else:
                self.face((a[i % na], b[(j + 1) % nb], b[j % nb]))
                j += 1
        return original

    def align(self, a, b):
        candidates = []
        for order in [b, list(reversed(b))]:
            for offset in range(len(b)):
                rotated = order[offset:] + order[:offset]
                cost = sum((self.vertices[a[i]] - self.vertices[rotated[round(i * len(b) / len(a)) % len(b)]]).
                           length_squared for i in range(len(a)))
                candidates.append((cost, rotated))
        return min(candidates, key=lambda item: item[0])[1]

    def cap(self, ring, weights=None):
        center = sum((self.vertices[i] for i in ring), Vector()) / len(ring)
        idx = self.vertex(center, weights or self.weights[ring[0]])
        for a, b in zip(ring, ring[1:] + ring[:1]):
            self.face((a, b, idx))

    def hole_loop(self, removed):
        counts, directed = {}, {}
        for face in removed:
            for a, b in zip(face, face[1:] + face[:1]):
                key = tuple(sorted((a, b)))
                counts[key] = counts.get(key, 0) + 1
                directed[key] = (a, b)
        edges = [directed[key] for key, count in counts.items() if count == 1]
        ring = [edges.pop(0)[0]]
        while edges:
            match = next((i for i, edge in enumerate(edges) if ring[-1] in edge), None)
            if match is None:
                break
            a, b = edges.pop(match)
            ring.append(b if a == ring[-1] else a)
        if ring[-1] == ring[0]:
            ring.pop()
        return ring

    def object(self):
        mesh = bpy.data.meshes.new(self.name + ' topology')
        mesh.from_pydata(self.vertices, [], self.faces)
        mesh.update()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.data.collections['GB15 Character'].objects.link(obj)
        obj.data.materials.append(self.mat)
        obj['gb_role'] = 'character'
        obj['gb_topology'] = 'New authored vertices and connectivity; no decimated source faces.'
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        names = sorted(set(name for entry in self.weights for name in entry))
        groups = {name: obj.vertex_groups.new(name=name) for name in names}
        for idx, weights in enumerate(self.weights):
            for name, value in weights.items():
                groups[name].add([idx], value, 'REPLACE')
        return obj


def ring(mesh, center, u, v, ru, rv, count, weights, phase=0):
    return [mesh.vertex(Vector(center) + u * (ru * math.cos(phase + i * math.tau / count)) +
                        v * (rv * math.sin(phase + i * math.tau / count)), weights) for i in range(count)]


def front_surface(x, z, fallback):
    hit = bpy.gb15_guide_bvh.ray_cast(Vector((x, -.45, z)), Vector((0, 1, 0)), .7)
    if hit[0] is None:
        return fallback
    return hit[0].y


def measure():
    result = []
    for obj in bpy.data.collections['GB15 Character'].objects:
        if obj.type != 'MESH':
            continue
        obj.data.calc_loop_triangles()
        result.append({'object': obj.name, 'vertices': len(obj.data.vertices),
                       'triangles': len(obj.data.loop_triangles)})
    report = {'parts': result, 'total_triangles': sum(row['triangles'] for row in result), 'limit': 15000}
    (ROOT / 'authoring/current_counts.json').write_text(json.dumps(report, indent=2) + '\n')
    return report
