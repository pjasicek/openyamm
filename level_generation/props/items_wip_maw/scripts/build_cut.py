"""Regular gem cuts built in Blender for the designs whose 'geometry' is a cut (designs.json): crisp facets that Smart
Topology rounds away. Table up, lowest point on the ground, longest side along Y; work/procedural/<design>.glb.

blender --background --python build_cut.py -- <design> [...]"""
import json
import math
import os
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))
OUT = os.path.join(HERE, 'work', 'procedural')
TAU = math.tau


def outline(shape, count):
    """Unit girdle outline, longest side along Y."""
    points = []
    for i in range(count):
        a = TAU * i / count
        x, y = math.cos(a), math.sin(a)
        if shape == 'cushion':
            # Rounded square: superellipse of power 4.
            x = math.copysign(abs(x) ** 0.5, x)
            y = math.copysign(abs(y) ** 0.5, y)
        elif shape == 'oval':
            y *= 1.25
        elif shape == 'pear':
            # Teardrop: the +Y end narrows to a point.
            t = (y + 1) / 2
            x *= 1 - 0.85 * t ** 2.2
            y *= 1.2
        points.append((x, y))
    return points


def faceted(shape, rings, count=16):
    """Rings of (radius, height, angular offset in steps): offsets alternate to make kite and star facets. Smaller
    rings close in on the outline's centroid, so a teardrop's dome peaks over its wide end."""
    base = outline(shape, count * 2)
    cy = sum(y for _, y in base) / len(base)
    vertices, faces = [], []
    for radius, height, offset in rings:
        for i in range(count):
            x, y = base[(2 * i + offset) % (2 * count)]
            vertices.append((x * radius, cy + (y - cy) * radius, height))
    n = len(rings)
    faces.append(tuple(reversed(range(count))))
    faces.append(tuple(range((n - 1) * count, n * count)))
    for r in range(n - 1):
        a, b = r * count, (r + 1) * count
        for i in range(count):
            j = (i + 1) % count
            faces.append((a + i, a + j, b + j, b + i))
    return vertices, faces


def prism(length, radius, tip):
    """Hexagonal crystal along Y with pyramid terminations, lying on a flat face."""
    vertices = []
    for y in (-length / 2, length / 2):
        for i in range(6):
            a = TAU * i / 6 + math.pi / 6
            vertices.append((radius * math.cos(a), y, radius * math.sin(a) + radius * math.sin(math.pi / 3)))
    vertices += [(0, -length / 2 - tip, radius * math.sin(math.pi / 3)),
                 (0, length / 2 + tip, radius * math.sin(math.pi / 3))]
    faces = [(i, (i + 1) % 6, 6 + (i + 1) % 6, 6 + i) for i in range(6)]
    faces += [((i + 1) % 6, i, 12) for i in range(6)] + [(6 + i, 6 + (i + 1) % 6, 13) for i in range(6)]
    return vertices, faces


def build(name):
    cut = DESIGNS[name]['geometry']['cut']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    smooth = False
    if cut in ('brilliant', 'cushion', 'oval'):
        shape = 'round' if cut == 'brilliant' else cut
        # Culet (a small flat point to rest on), pavilion, girdle band, crown, table.
        vertices, faces = faceted(shape, [(0.10, 0.0, 0), (0.62, 0.30, 1), (1.0, 0.52, 0), (1.0, 0.57, 0),
                                          (0.80, 0.76, 1), (0.56, 0.88, 0)])
    elif cut == 'cabochon':
        rings = [(1.0, 0.0, 0)] + [(math.cos(t), 0.04 + 0.5 * math.sin(t), 0)
                                   for t in (k * math.pi / 2 / 7 for k in range(0, 7))] + [(0.08, 0.55, 0)]
        vertices, faces = faceted('pear', rings, 24)
        smooth = True
    elif cut == 'prism':
        aspect = DESIGNS[name]['geometry']['aspect']
        vertices, faces = prism(aspect, 0.5, 0.45)
    elif cut == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.5, location=(0, 0, 0.5))
        obj = bpy.context.object
        smooth = True
    if cut != 'sphere':
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
    obj.name = name
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    for polygon in obj.data.polygons:
        polygon.use_smooth = smooth
    lowest = min(v.co.z for v in obj.data.vertices)
    for v in obj.data.vertices:
        v.co.z -= lowest
    os.makedirs(OUT, exist_ok=True)
    for other in bpy.data.objects:
        other.select_set(other == obj)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{name}.glb'), use_selection=True, export_format='GLB',
                              export_yup=True, export_materials='NONE')
    print('CUT', name, cut, len(obj.data.polygons), 'triangles')


for design in sys.argv[sys.argv.index('--') + 1:]:
    build(design)
