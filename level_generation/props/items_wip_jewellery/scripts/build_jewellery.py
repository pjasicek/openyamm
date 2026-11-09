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
from surface_detail import engrave

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
    if colour not in GEM_COLOURS:
        return core
    # A separate reflective glass shell exposes the coloured pavilion around the solid core's silhouette.
    shell = core.copy()
    shell.data = core.data.copy()
    shell.name = 'Glass ' + core.name
    bpy.context.collection.objects.link(shell)
    shell['jewellery_glass'] = True
    key = colour + '_glass'
    if key not in MATERIALS:
        glass = material(colour).copy()
        glass.name = key
        shader = glass.node_tree.nodes['Principled BSDF']
        source = shader.inputs['Base Color'].default_value[:]
        shader.inputs['Base Color'].default_value = (*source[:3], 1)
        shader.inputs['Alpha'].default_value = .32
        shader.inputs['Roughness'].default_value = .045
        glass.surface_render_method = 'DITHERED'
        MATERIALS[key] = glass
    shell.data.materials.clear()
    shell.data.materials.append(MATERIALS[key])
    key = colour + '_core'
    if key not in MATERIALS:
        mat = material(colour).copy()
        mat.name = key
        shader = mat.node_tree.nodes['Principled BSDF']
        source = shader.inputs['Base Color'].default_value[:]
        factor = .8 if colour == 'diamond' else .55
        shader.inputs['Base Color'].default_value = (*[max(linear(30 / 255), channel * factor)
                                                     for channel in source[:3]], 1)
        shader.inputs['Roughness'].default_value = .07
        MATERIALS[key] = mat
    core.data.materials.clear()
    core.data.materials.append(MATERIALS[key])
    lower = Vector([min(v.co[i] for v in core.data.vertices) for i in range(3)])
    upper = Vector([max(v.co[i] for v in core.data.vertices) for i in range(3)])
    centre = (lower + upper) / 2
    for vertex in core.data.vertices:
        vertex.co = centre + (vertex.co - centre) * .96
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


def ring(icon):
    silver = icon in {'7item122', '7item124', '7item125', '7item127', '7item128', '7item302', '7item303',
                      'item139', 'item142', 'item143', 'item146', 'ring2', 'ring7'}
    metal = 'silver' if silver else ('bronze' if icon in {'7item120', 'item137', 'item345'} else 'gold')
    broad_band = {'item137', 'item138', 'item139', 'item140', 'item141', 'item332', 'item338', 'item345'}
    width = .14 if icon in broad_band else .10
    if icon in {'6ring11', '6ring13', 'ring9'}:
        width = .20
    if icon in {'7item129', '7item284'}:
        for y in (-.07, .07):
            rail = hoop('Open lattice rail', .36, .36, 0, .025, .024, metal)
            rail.rotation_euler.x = math.pi / 2
            rail.location.y = y
        for i in range(16):
            a = TAU * i / 16
            bar = box('Lattice bridge', (.36 * math.sin(a), 0, .36 * math.cos(a)), (.026, .14, .035), metal, .003)
            bar.rotation_euler.y = a
    else:
        band = hoop('Open ring band', .36, .36, 0, .035, width, metal)
        if icon in {'6ring11', '6ring13', 'ring9', 'ring1', 'ring2', 'ring3', 'ring4', 'ring5', 'ring6',
                    'ring7', 'ring8', 'ring10', '6ring12', '6ring14', 'item140', 'item332', 'item144'}:
            engrave(band, 1 if metal == 'silver' else 0, band=True)
        elif icon == '7item122':
            engrave(band, 1, band=True)
        band.rotation_euler.x = math.pi / 2
    z = .37
    if icon in {'7item120', 'item137', 'item345'}:
        pass
    elif icon in {'item138', '7item122', 'ring6'}:
        for y in (-width / 2, width / 2):
            edge = hoop('Band edge', .365, .365, y, .012, .018, metal)
            edge.rotation_euler.x = math.pi / 2
        if icon != 'item138':
            for i in range(16):
                a = TAU * i / 16
                obj = ball('Fluted band', (.385 * math.sin(a), 0, .385 * math.cos(a)), (.023, .05, .052), metal, 1)
                obj.rotation_euler.y = a
    if icon in {'6ring11', '6ring13', 'ring9'}:
        setting(0, 0, z, .32, .44, 'jade')
    elif icon in {'6ring12', '6ring14', 'ring10'}:
        body = setting(0, 0, z, .37, .42, 'red')
        engrave(body, 7)
        for side in (-1, 1):
            setting(side * .28, -.04, z - .05, .13, .14, 'amber')
            tube('Scarab horn', [(side * .15, .11, z + .10), (side * .29, .17, z + .12),
                                 (side * .33, .25, z + .22)], .035, 'pearl', True)
        for side in (-1, 1):
            tube('Scarab gold lattice', [(side * .1, -.15, z + .20), (side * .11, -.06, z + .25),
                                         (side * .09, .07, z + .26), (side * .07, .16, z + .19)], .016, 'gold')
        setting(0, .18, z + .05, .10, .10, 'amber')
    elif icon in {'7item121', 'item139', 'ring1'}:
        setting(0, 0, z, .20, .20, 'pearl', metal)
    elif icon == '7item123':
        setting(0, 0, z, .30, .29, 'green', metal, 'emerald')
        for x in (-.23, .23):
            setting(x, 0, z - .075, .10, .10, 'diamond', metal)
    elif icon == '7item124':
        for x in (-.21, 0, .21):
            setting(x, 0, z - abs(x) * .3, .24 if x == 0 else .14, .20, 'blue', metal)
        setting(0, 0, z + .12, .10, .09, 'pearl', metal)
    elif icon == '7item125':
        setting(0, 0, z, .23, .40, 'purple', 'gold', 'marquise')
        for x in (-.20, .20):
            setting(x, .12, z, .13, .13, 'purple')
            tube('Gold scroll', [(x, -.17, z), (x * 1.3, -.08, z + .02), (x * 1.1, .13, z + .03)], .022, 'gold')
        setting(0, -.20, z, .085, .085, 'green')
    elif icon == '7item126':
        setting(0, 0, z, .36, .42, 'green', 'silver', 'square')
        stone('Purple inlay', (0, 0, z + .22), (.15, .18, .04), 'purple', 'square')
    elif icon in {'7item127', '7item303'}:
        setting(0, 0, z, .24, .24, 'green')
        colours = ['red', 'purple', 'blue', 'yellow', 'red', 'purple', 'amber', 'blue']
        for i, colour in enumerate(colours):
            a = TAU * i / len(colours)
            setting(.23 * math.cos(a), .23 * math.sin(a), z - .035, .12, .12, colour)
    elif icon in {'7item128', '7item302'}:
        for x in (-.24, 0, .24):
            setting(x, 0, z - abs(x) * .3, .23, .28, 'purple', 'silver', 'square')
    elif icon in {'7item129', '7item284'}:
        setting(0, 0, z, .34, .34, 'amber', 'gold', 'triangle')
        for i in range(18):
            a = TAU * i / 18
            ball('Red band inlay', (.38 * math.sin(a), -.04, .38 * math.cos(a)), (.027, .027, .027), 'red', 1)
    elif icon == '7item246':
        outer = [(math.cos(TAU * i / 8) * (.28 if i % 2 == 0 else .07),
                  math.sin(TAU * i / 8) * (.34 if i % 2 == 0 else .07)) for i in range(8)]
        plate('Gold star', outer, z, .035, 'gold')
        plate('Icy star', [(x * .79, y * .79) for x, y in outer], z + .035, .025, 'cyan')
        enamel = hoop('Blue enamel', .397, .397, 0, .006, .075, 'blue')
        enamel.rotation_euler.x = math.pi / 2
    elif icon in {'item140', 'item332'}:
        for x in (-.26, -.13, 0, .13, .26):
            setting(x, 0, z - abs(x) * .35, .09, .09, 'yellow')
    elif icon in {'item141', 'item338'}:
        setting(0, 0, z, .23, .23, 'red')
    elif icon in {'item142', 'item144'}:
        skull(z, metal, icon == 'item144')
        for side in (-1, 1):
            if icon == 'item144':
                wing = [(side * x, y) for x, y in [(.1, .08), (.28, .06), (.48, -.19),
                                                  (.30, -.1), (.23, -.22), (.17, -.13), (.10, -.20)]]
                plate('Bat wing', wing, z, .045, metal)
            else:
                for i in range(4):
                    x = side * (.15 + i * .047)
                    ball('Rib shoulder', (x, 0, z - i * .035), (.025, .065, .035), metal, 1)
    elif icon == 'item143':
        for x in (-.25, 0, .25):
            setting(x, 0, z - abs(x) * .4, .27 if x == 0 else .14, .24 if x == 0 else .14, 'purple', metal)
    elif icon == 'item145':
        outline_star = [(math.cos(TAU * i / 32) * (.28 if i % 2 == 0 else .21),
                         math.sin(TAU * i / 32) * (.28 if i % 2 == 0 else .21)) for i in range(32)]
        plate('Sunburst', outline_star, z, .025, 'gold')
        setting(0, 0, z + .025, .31, .31, 'yellow')
        for i in range(12):
            a = TAU * i / 12
            ball('Ruby halo', (.22 * math.cos(a), .22 * math.sin(a), z + .06), (.025, .025, .025), 'red', 1)
    elif icon == 'item146':
        setting(0, .03, z, .30, .32, 'pearl', metal)
        for side in (-1, 1):
            tube('Open scroll', [(side * .22, .10, z), (side * .24, -.12, z),
                                 (side * .12, -.23, z), (side * .08, -.15, z)], .024, metal)
            setting(side * .10, -.17, z + .015, .09, .09, 'pearl', metal)
    elif icon == 'ring2':
        for x in (-.14, .14):
            setting(x, 0, z, .24, .27, 'purple', 'gold')
        stone('Crown spike', (0, .16, z), (.10, .12, .16), 'silver', 'square')
    elif icon == 'ring3':
        setting(0, 0, z, .28, .37, 'blue', 'gold', 'emerald')
        for x in (-.28, .28):
            setting(x, 0, z - .06, .14, .34, 'red', 'silver', 'marquise')
    elif icon == 'ring5':
        setting(0, 0, z, .24, .24, 'red')
        for x in (-.25, .25):
            setting(x, 0, z - .07, .21, .29, 'purple')
    elif icon == 'ring6':
        setting(0, 0, z, .31, .30, 'diamond', 'silver', 'round')
        for x in (-.27, .27):
            setting(x, 0, z - .06, .20, .25, 'pearl')
    elif icon == 'ring7':
        for x in (-.26, 0, .26):
            setting(x, .015, z - abs(x) * .18, .19, .24, 'cyan')
            for i in range(6):
                a = TAU * i / 6
                ball('Beaded surround', (x + .11 * math.cos(a), .015 + .14 * math.sin(a), z + .015 - abs(x) * .18),
                     (.018, .018, .018), 'gold', 1)
    elif icon == 'ring8':
        for x in (-.23, 0, .23):
            setting(x, .04, z - abs(x) * .2, .13, .30, 'jade')
        for i in range(9):
            ball('Gold beads', ((i - 4) * .075, -.13, z - abs(i - 4) * .018), (.034, .034, .034), 'gold', 1)
    if icon in {'ring1', 'ring2', 'ring4'}:
        for side in (-1, 1):
            tube('Crescent shoulder', [(side * .18, 0, z), (side * .30, .04, z + .04),
                                      (side * .38, .13, z + .12)], .055, 'silver', True)
        if icon == 'ring4':
            for side in (-1, 1):
                tube('Inner crescent', [(side * .08, 0, z), (side * .15, .11, z + .09),
                                       (side * .08, .23, z + .14)], .048, 'silver', True)
    # A ring lies supported by its shank and setting; the open centre stays visible from above.
    return Matrix.Rotation(math.radians(62), 4, 'X')


GEMS = {
    '7item195': ('emerald', 'green', (1, .57, .34)),
    '7item196': ('round', 'diamond', (1, .80, .46)),
    '7item197': ('emerald', 'green', (.65, 1, .45)),
    '7item198': ('octagon', 'amber', (1, .85, .42)),
    '7item199': ('quartz', 'cyan', (1, .30, .28)),
    '7item202': ('round', 'blue', (1, .68, .42)),
    '7item203': ('quartz', 'pink', (1, .42, .36)),
    '7item204': ('hexagon', 'purple', (1, .70, .48)),
    'gem1': ('orb', 'diamond', (1, 1, .85)), 'gem10': ('orb', 'cyan', (1, 1, .82)),
    'gem2': ('marquise', 'cyan', (.43, 1, .38)), 'gem3': ('rose_triangle', 'yellow', (1, 1, .48)),
    'gem4': ('rose_square', 'red', (1, 1, .48)), 'gem5': ('rose_pentagon', 'blue', (1, 1, .48)),
    'gem6': ('rose_hexagon', 'green', (1, 1, .48)), 'gem7': ('rose_octagon', 'purple', (1, 1, .50)),
    'gem8': ('orb', 'amber', (1, 1, .85)), 'gem9': ('pear', 'peridot', (.90, 1, .54)),
    'item212': ('square', 'pink', (.83, 1, .52)), 'item213': ('pentagon', 'yellow', (1, 1, .45)),
    'item214': ('octagon', 'amber', (.82, 1, .50)), 'item215': ('round', 'amber', (1, .70, .42)),
    'item216': ('round', 'diamond', (.83, 1, .53)), 'item217': ('round', 'blue', (1, .80, .50)),
    'item218': ('round', 'purple', (1, .56, .38)), 'item219': ('round', 'green', (1, .75, .45)),
    'item220': ('octagon', 'purple', (.91, 1, .52)), 'item221': ('round', 'amber', (1, .73, .44)),
}


def gem(icon):
    kind, colour, size = GEMS[icon]
    if kind == 'orb':
        obj = ball('Faceted orb', (0, 0, size[2] / 2), (size[0] / 2, size[1] / 2, size[2] / 2), colour)
        for face in obj.data.polygons:
            face.use_smooth = False
        glass_shell(obj, colour)
    elif kind == 'quartz':
        vertices = []
        for x, radius in [(-.5, .025), (-.35, .18), (.35, .5), (.5, .38)]:
            for i in range(6):
                vertices.append((x, size[1] * radius * math.cos(TAU * i / 6),
                                 size[2] * radius * math.sin(TAU * i / 6)))
        faces = [tuple(reversed(range(6))), tuple(range(18, 24))]
        for level in range(3):
            for i in range(6):
                faces.append((level * 6 + i, level * 6 + (i + 1) % 6,
                              (level + 1) * 6 + (i + 1) % 6, (level + 1) * 6 + i))
        glass_shell(mesh('Terminated crystal prism', vertices, faces, colour), colour)
    else:
        stone('Cut ' + colour, (0, 0, 0), size, colour, kind)
    return Matrix.Identity(4)


def finish(row, rotation):
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for obj in objects:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if not obj.data.uv_layers:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(island_margin=.015)
            bpy.ops.object.mode_set(mode='OBJECT')
        assert len(obj.data.uv_layers) == 1, obj.name
        obj.data.uv_layers.active.name = 'UVMap'
    name = 'jewellery_' + row['icon']
    groups = [[obj for obj in objects if bool(obj.get('jewellery_glass')) == glass] for glass in (False, True)]
    objects = []
    for group in groups:
        if not group:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        for obj in group:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = group[0]
        if len(group) > 1:
            bpy.ops.object.join()
        obj = bpy.context.object
        obj.name = name + ('_glass' if obj.get('jewellery_glass') else '')
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        obj.data.transform(rotation)
        objects.append(obj)
    points = [v.co for obj in objects for v in obj.data.vertices]
    low = Vector([min(p[i] for p in points) for i in range(3)])
    high = Vector([max(p[i] for p in points) for i in range(3)])
    shift = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    triangles = 0
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        for vertex in obj.data.vertices:
            vertex.co -= shift
        if high.x - low.x > high.y - low.y:
            obj.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Z'))
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        assert not any(not edge.is_manifold for edge in bm.edges), row['icon'] + ': open component'
        assert all(face.calc_area() > 1e-10 for face in bm.faces), row['icon'] + ': degenerate face'
        triangles += len(bm.faces)
        bm.to_mesh(obj.data)
        bm.free()
        obj.select_set(True)
    assert 0 < triangles <= 3200, (row['icon'], triangles)
    export = PROJECT / 'work/exports' / (name + '_export.glb')
    export.parent.mkdir(parents=True, exist_ok=True)
    blend = PROJECT / 'blends' / (name + '.blend')
    blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(export), export_format='GLB', use_selection=True,
                              export_yup=True, export_materials='EXPORT', export_cameras=False,
                              export_animations=False, export_extras=True)
    return {'icon': row['icon'], 'export': str(export.relative_to(PROJECT)),
            'triangles': triangles, 'binding_length': row['length']}


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = set(args)
    receipts = PROJECT / 'work/build_receipts.json'
    records = json.loads(receipts.read_text()) if receipts.exists() else {}
    for row in json.loads((PROJECT / 'ownership.json').read_text()):
        icon = row['icon']
        if icon in KEEP or (only and icon not in only):
            continue
        if row['family'] == 'belts' or icon == 'item211':
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        MATERIALS.clear()
        rotation = ring(icon) if row['family'] == 'rings' else gem(icon)
        records[icon] = finish(row, rotation)
        receipts.write_text(json.dumps(records, indent=2) + '\n')
        print('BUILT', icon, records[icon]['triangles'], flush=True)


if __name__ == '__main__':
    main()
