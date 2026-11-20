"""Icon-reviewed jewellery geometry; isolated Blender process, no runtime installation.

blender --background --python build_jewellery.py -- [icon ...]
"""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))


PROJECT = Path(__file__).resolve().parents[1]
TAU = math.tau
KEEP = {'7item146', '7item154', '7item264'}
PALETTE = {
    'gold': ('d8af53', 1, .29), 'silver': ('c4cbd2', 1, .28), 'bronze': ('ad7957', 1, .34),
    'dark': ('292b32', 0, .56), 'red': ('b72b42', 0, .16), 'purple': ('792bb3', 0, .18),
    'blue': ('244bcb', 0, .15), 'cyan': ('57bacb', 0, .17), 'green': ('24a05a', 0, .18),
    'jade': ('314e43', 0, .2), 'yellow': ('e4b53a', 0, .18), 'amber': ('d57929', 0, .2),
    'pink': ('c95698', 0, .2), 'diamond': ('b5cfdf', 0, .12), 'pearl': ('dcd5ba', 0, .26),
    'peridot': ('94ba45', 0, .18),
}
MATERIALS = {}
GEM_COLOURS = {'red', 'purple', 'blue', 'cyan', 'green', 'yellow', 'amber', 'pink', 'diamond', 'peridot'}


def linear(value):
    return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4


def material(name):
    if name in MATERIALS:
        return MATERIALS[name]
    colour, metal, rough = PALETTE[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*[linear(int(colour[i:i + 2], 16) / 255) for i in (0, 2, 4)], 1)
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = rough
    MATERIALS[name] = mat
    return mat


def mesh(name, vertices, faces, mat, smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(material(mat))
    for polygon in data.polygons:
        polygon.use_smooth = smooth
    return obj


def ball(name, position, size, mat, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    obj.data.materials.append(material(mat))
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def glass_shell(core, colour):
    return core


def box(name, position, size, mat, bevel=.01):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material(mat))
    if bevel:
        modifier = obj.modifiers.new('Readable edge bevel', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 1
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def hoop(name, rx, ry, z, radial, width, mat, segments=32, bevel=True):
    # Eight-sided bevelled band profile; actual open centre, with closed inner/outer walls.
    profile = [(-.7, -.5), (.7, -.5), (1, -.3), (1, .3), (.7, .5), (-.7, .5), (-1, .3), (-1, -.3)]
    if not bevel:
        profile = [(-1, -.5), (1, -.5), (1, .5), (-1, .5)]
    count = len(profile)
    vertices = []
    for i in range(segments):
        angle = TAU * i / segments
        for dr, dz in profile:
            vertices.append(((rx + dr * radial) * math.cos(angle),
                             (ry + dr * radial) * math.sin(angle), z + dz * width))
    faces = []
    for i in range(segments):
        for j in range(count):
            faces.append((i * count + j, ((i + 1) % segments) * count + j,
                          ((i + 1) % segments) * count + (j + 1) % count, i * count + (j + 1) % count))
    return mesh(name, vertices, faces, mat, True)


def tube(name, points, radius, mat, taper=False):
    vertices = []
    for i, p in enumerate(points):
        p = Vector(p)
        tangent = Vector(points[min(i + 1, len(points) - 1)]) - Vector(points[max(0, i - 1)])
        tangent.normalize()
        normal = tangent.cross(Vector((0, 1, 0)))
        if normal.length < .01:
            normal = tangent.cross(Vector((1, 0, 0)))
        normal.normalize()
        other = tangent.cross(normal)
        r = radius * (max(.09, 1 - i / (len(points) - 1)) if taper else 1)
        for j in range(6):
            vertices.append(p + r * (normal * math.cos(TAU * j / 6) + other * math.sin(TAU * j / 6)))
    faces = []
    for i in range(len(points) - 1):
        for j in range(6):
            faces.append((i * 6 + j, i * 6 + (j + 1) % 6, (i + 1) * 6 + (j + 1) % 6, (i + 1) * 6 + j))
    faces += [tuple(reversed(range(6))), tuple((len(points) - 1) * 6 + j for j in range(6))]
    return mesh(name, vertices, faces, mat, True)


def plate(name, outline, bottom, depth, mat):
    count = len(outline)
    vertices = [(x, y, bottom + z) for z in (0, depth) for x, y in outline]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    faces += [(i, (i + 1) % count, (i + 1) % count + count, i + count) for i in range(count)]
    return mesh(name, vertices, faces, mat)


def outline(kind):
    if kind == 'emerald':
        return [(-.72, -1), (.72, -1), (1, -.72), (1, .72), (.72, 1), (-.72, 1), (-1, .72), (-1, -.72)]
    if kind == 'marquise':
        return [(0, -1), (.65, -.5), (1, 0), (.65, .5), (0, 1), (-.65, .5), (-1, 0), (-.65, -.5)]
    if kind == 'pear':
        return [(0, 1), (.50, .50), (.80, -.1), (.66, -.7), (0, -1), (-.66, -.7), (-.80, -.1), (-.50, .50)]
    count = {'triangle': 3, 'square': 4, 'pentagon': 5, 'hexagon': 6, 'octagon': 8}.get(kind, 16)
    return [(math.cos(TAU * i / count), math.sin(TAU * i / count)) for i in range(count)]


def stone(name, position, size, colour, kind='round'):
    if kind == 'pearl':
        obj = ball(name, (position[0], position[1], position[2] + size[2] / 2),
                   (size[0] / 2, size[1] / 2, size[2] / 2), colour)
        return glass_shell(obj, colour)
    rose = kind.startswith('rose_')
    shape = outline(kind.removeprefix('rose_'))
    n = len(shape)
    levels = [(.14, 0), (1, .35), (1, .42), (.76, .78), (.48, 1)]
    if rose:
        levels = [(.14, 0), (1, .35), (.92, .48)]
    vertices = []
    for level, (radius, height) in enumerate(levels):
        for index, (x, y) in enumerate(shape):
            if kind == 'round' and level == 3:
                angle = TAU * (index + .5) / n
                x, y = math.cos(angle), math.sin(angle)
            vertices.append((position[0] + x * radius * size[0] / 2,
                             position[1] + y * radius * size[1] / 2, position[2] + height * size[2]))
    faces = [tuple(reversed(range(n)))]
    if rose:
        apex = len(vertices)
        vertices.append((position[0], position[1], position[2] + size[2]))
        faces += [((len(levels) - 1) * n + i, (len(levels) - 1) * n + (i + 1) % n, apex) for i in range(n)]
    else:
        faces.append(tuple(range((len(levels) - 1) * n, len(levels) * n)))
    for level in range(len(levels) - 1):
        for j in range(n):
            k = (j + 1) % n
            faces.append((level * n + j, level * n + k, (level + 1) * n + k, (level + 1) * n + j))
    return glass_shell(mesh(name, vertices, faces, colour), colour)


def setting(x, y, z, sx, sy, colour, metal='gold', kind='pearl'):
    if kind in {'square', 'emerald', 'marquise'}:
        shape = outline(kind)
        count = len(shape)
        vertices = [(x + px * sx / 2 * radius, y + py * sy / 2 * radius, z + height)
                    for radius, height in [(1.14, .0025), (1.14, .0475), (1, .0475), (1, .0025)]
                    for px, py in shape]
        faces = [(layer * count + i, layer * count + (i + 1) % count,
                  ((layer + 1) % 4) * count + (i + 1) % count, ((layer + 1) % 4) * count + i)
                 for layer in range(4) for i in range(count)]
        mesh('Shaped bezel', vertices, faces, metal)
    else:
        bezel = hoop('Raised bezel', sx / 2, sy / 2, z + .025, .014, .045, metal, 12, bevel=False)
        bezel.location.x, bezel.location.y = x, y
    return stone('Set ' + colour, (x, y, z), (sx, sy, min(sx, sy) * .65), colour, kind)


def skull(z, metal='silver', vampire=False):
    ball('Skull cranium', (0, .025, z + .06), (.135, .14, .075), metal)
    box('Jaw', (0, -.09, z + .035), (.15, .10, .08), metal, .018)
    for side in (-1, 1):
        ball('Eye socket', (side * .052, -.025, z + .135), (.038, .043, .018), 'red' if vampire else 'dark', 1)
        if vampire:
            tube('Horn', [(side * .1, .08, z + .08), (side * .16, .14, z + .12),
                          (side * .14, .23, z + .14)], .03, metal, True)
    plate('Nasal cavity', [(-.018, -.085), (.018, -.085), (0, -.045)], z + .12, .008, 'dark')
    for i in range(4):
        box('Tooth', ((i - 1.5) * .031, -.13, z + .073), (.023, .032, .024), metal, .002)

