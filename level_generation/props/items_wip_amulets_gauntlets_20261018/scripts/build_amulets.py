"""Volumetric pendants: real settings, backs, gems, bails and interlinked chain loops.

Uses the project's existing jewellery primitives, frozen locally to avoid changing another worker's code.
Blender --background --python build_amulets.py -- [icon ...]
"""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import primitives as g

TAU = math.tau
MATERIALS = {}
ALIASES = {'green': 'jade', 'pearl': 'ivory', 'yellow': 'amber', 'cyan': 'turquoise'}
GROUPS = {'6amulet6': 'amulet5', '6amulet7': 'amulet5', '6amulet8': 'amulet5',
          '7item285': '7item134', '7item287': '7item133'}


def material(name):
    name = ALIASES.get(name, name)
    if name in MATERIALS:
        return MATERIALS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    images = {}
    for kind in ('basecolor', 'mr', 'normal'):
        node = nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(P / f'textures/{name}_{kind}.png'), check_existing=True)
        if kind != 'basecolor':
            node.image.colorspace_settings.name = 'Non-Color'
        images[kind] = node
    links.new(images['basecolor'].outputs['Color'], shader.inputs['Base Color'])
    split = nodes.new('ShaderNodeSeparateColor')
    links.new(images['mr'].outputs['Color'], split.inputs['Color'])
    links.new(split.outputs['Green'], shader.inputs['Roughness'])
    links.new(split.outputs['Blue'], shader.inputs['Metallic'])
    normal = nodes.new('ShaderNodeNormalMap')
    links.new(images['normal'].outputs['Color'], normal.inputs['Color'])
    links.new(normal.outputs['Normal'], shader.inputs['Normal'])
    MATERIALS[name] = mat
    return mat


g.material = material


def ring(x, y, rx, ry, z=.045, wire=.018, metal='gold', segments=20):
    obj = g.hoop('Closed metal ring', rx, ry, z, wire, wire * 2, metal, segments, bevel=False)
    obj.location.x, obj.location.y = x, y
    return obj


def bail(y=.5, metal='gold', x=0, radius=.06):
    return ring(x, y, radius, radius * 1.25, .06, .017, metal, 16)


def chain(rx=.30, ry=.74, cy=1.13, count=42, metal='gold', rope=False):
    if rope:
        points = [(rx * math.sin(TAU * i / 56), cy + ry * math.cos(TAU * i / 56), .04)
                  for i in range(57)]
        return g.tube('Braided necklace cord', points, .022, metal)
    # Oval links alternate between shallow and upright planes; their centres follow one necklace loop.
    for i in range(count):
        a = TAU * i / count
        centre = Vector((rx * math.sin(a), cy + ry * math.cos(a), .045))
        tangent = Vector((rx * math.cos(a), -ry * math.sin(a), 0)).normalized()
        side = Vector((-tangent.y, tangent.x, 0))
        side = side * math.cos(.9 if i % 2 else -.5) + Vector((0, 0, 1)) * math.sin(.9 if i % 2 else -.5)
        verts = []
        for j in range(10):
            b = TAU * j / 10
            axis = tangent * math.cos(b) + side * math.sin(b)
            for k in range(4):
                c = TAU * k / 4
                verts.append(centre + tangent * (.055 * math.cos(b)) + side * (.026 * math.sin(b))
                             + .009 * (axis * math.cos(c) + tangent.cross(side) * math.sin(c)))
        faces = [(j * 4 + k, ((j + 1) % 10) * 4 + k,
                  ((j + 1) % 10) * 4 + (k + 1) % 4, j * 4 + (k + 1) % 4)
                 for j in range(10) for k in range(4)]
        g.mesh('Interlinked oval necklace link', verts, faces, metal, True)


def scroll(cx, cy, sx=.15, sy=.15, metal='gold', mirror=1):
    points = []
    for i in range(16):
        a = -1.2 + i / 15 * 5.1
        radius = 1 - .75 * i / 15
        points.append((cx + mirror * sx * radius * math.cos(a), cy + sy * radius * math.sin(a), .11))
    g.tube('Raised curling filigree', points, .017, metal)


def oval_body(rx, ry, colour, metal='gold', beaded=False):
    g.ball('Convex pendant back', (0, 0, .035), (rx, ry, .055), metal)
    ring(0, 0, rx, ry, .075, .022, metal)
    if colour in ('dark', 'bronze'):
        g.ball('Recessed medallion field', (0, 0, .065), (rx * .92, ry * .92, .035), colour)
    else:
        g.stone('Raised cabochon', (0, 0, .04), (rx * 1.78, ry * 1.78, .18), colour, 'pearl')
    if beaded:
        for i in range(28):
            a = TAU * i / 28
            g.ball('Individual border bead', (rx * 1.06 * math.cos(a), ry * 1.06 * math.sin(a), .075),
                   (.022, .022, .024), metal, 1)


def star(rx=.42, ry=.45, inner=.38, points=8, bottom=.025, depth=.09, metal='gold'):
    outline = [(math.sin(TAU * i / (points * 2)) * rx * (1 if i % 2 == 0 else inner),
                math.cos(TAU * i / (points * 2)) * ry * (1 if i % 2 == 0 else inner))
               for i in range(points * 2)]
    if metal == 'red':
        n = len(outline)
        vertices = [(x * radius, y * radius, bottom + height * depth)
                    for radius, height in [(1, 0), (1, .25), (.76, .8), (.2, 1)] for x, y in outline]
        faces = [tuple(reversed(range(n))), tuple(range(3 * n, 4 * n))]
        faces += [(j * n + i, j * n + (i + 1) % n, (j + 1) * n + (i + 1) % n, (j + 1) * n + i)
                  for j in range(3) for i in range(n)]
        return g.mesh('Faceted ruby star crown', vertices, faces, metal)
    return g.plate('Raised star setting', outline, bottom, depth, metal)


def skull_at(x=0, y=0, scale=1, metal='silver', red=False):
    before = set(bpy.context.scene.objects)
    g.ball('Skull cranium', (0, .08, .10), (.15, .17, .038), metal, 3)
    g.box('Skull jaw', (0, -.13, .105), (.19, .13, .055), metal, .015)
    for s in (-1, 1):
        g.ball('Skull cheek', (s * .10, -.03, .11), (.06, .06, .026), metal, 2)
        g.ball('Eye socket', (s * .065, .06, .135), (.04, .047, .009), 'dark', 2)
        if red:
            g.ball('Tiny ruby eye inlay', (s * .065, .06, .144), (.019, .021, .006), 'red', 2)
    g.plate('Nasal recess', [(-.024, -.07), (.024, -.07), (0, -.025)], .137, .006, 'dark')
    for i in range(5):
        g.box('Skull tooth', ((i - 2) * .033, -.17, .133), (.025, .045, .018), metal, .003)
    for obj in set(bpy.context.scene.objects) - before:
        obj.location = Vector((x, y, .02)) + obj.location * scale
        obj.scale *= scale


def spline(points, steps=5, closed=False):
    p = [Vector(v) for v in points]
    output = []
    for i in range(len(p) if closed else len(p) - 1):
        a, b, c, d = [p[k % len(p)] if closed else p[max(0, min(k, len(p) - 1))]
                      for k in (i - 1, i, i + 1, i + 2)]
        for j in range(steps):
            t = j / steps
            output.append(tuple(.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                                      + (-a + 3 * b - 3 * c + d) * t * t * t)))
    if not closed:
        output.append(tuple(p[-1]))
    return output


original_tube, original_plate = g.tube, g.plate


def curved_tube(name, points, radius, mat, taper=False):
    if len(points) < 8 and not any(word in name.lower() for word in ('finger', 'pictogram', 'thumb')):
        points = spline(points)
    return original_tube(name, points, radius, mat, taper)


def curved_plate(name, outline, bottom, depth, mat):
    if name.startswith('Curved'):
        outline = [v[:2] for v in spline([(x, y, 0) for x, y in outline], closed=True)]
    return original_plate(name, outline, bottom, depth, mat)


g.tube, g.plate = curved_tube, curved_plate


def make(icon):
    if icon == 'amulet5':
        chain(rx=.25)
        bail(.37)
        star(.39, .42)
        star(.29, .31, .28, bottom=.12, depth=.09, metal='red')
        for s in (-1, 1):
            scroll(s * .32, .23, .15, .15, mirror=s)
            scroll(s * .32, -.22, .15, -.15, mirror=s)
    elif icon == 'amulet1':
        chain(rx=.37)
        bail(.36)
        oval_body(.25, .39, 'turquoise')
        for s in (-1, 1):
            for y in (-.24, 0, .24):
                g.tube('Curving gold setting claw', [(s * .21, y - .06, .06),
                       (s * .34, y, .10), (s * .28, y + .11, .12)], .035, 'gold', True)
    elif icon == 'amulet2':
        chain(rx=.26)
        bail(.34)
        g.stone('Angular pyramid pendant', (0, 0, .02), (.74, .76, .23), 'bronze', 'triangle')
        for a in (0, TAU / 3, TAU * 2 / 3):
            points = [(.20 * math.cos(a), .20 * math.sin(a), .08),
                      (.43 * math.cos(a + .25), .43 * math.sin(a + .25), .14),
                      (.45 * math.cos(a + .9), .45 * math.sin(a + .9), .16)]
            g.tube('Three curved talons', points, .06, 'ivory', True)
        for a in (0, TAU / 3, TAU * 2 / 3):
            g.ball('Pyramid raised stud', (.11 * math.cos(a), .11 * math.sin(a), .2), (.022, .022, .02), 'gold', 1)
    elif icon == 'amulet3':
        chain(rx=.17, ry=.75, cy=1.02, metal='bronze', rope=True)
        oval_body(.22, .29, 'purple', 'bronze')
        for x in (-.23, 0, .23):
            g.tube('Long claw prong', [(x, -.25, .05), (x * 1.35, .12, .12),
                    (x * 1.05 + .12, .42 + (.1 if x == 0 else 0), .13)], .055, 'ivory', True)
    elif icon == 'amulet4':
        chain(rx=.36, ry=.66, cy=1.04)
        bail(.34)
        g.box('Gilded tablet frame', (0, 0, .06), (.87, .33, .12), 'gold', .025)
        g.tube('Tablet suspension neck', [(0, .16, .10), (0, .24, .08), (0, .29, .06)], .019, 'gold')
        g.box('Ivory tablet face', (0, 0, .125), (.74, .23, .035), 'ivory', .006)
        for x in (-.39, .39):
            g.box('Red enamel end inlay', (x, 0, .13), (.034, .25, .025), 'red', .003)
        # Deliberate source-like angular pictograms, raised a fraction above the enamel.
        for outline in [[(-.29, .06), (-.29, -.05), (-.20, -.05), (-.20, .015)],
                        [(-.10, .065), (-.04, .065), (-.04, -.015), (.025, -.015), (.025, -.05), (.10, -.05)],
                        [(.16, .055), (.16, -.03), (.25, -.03), (.25, .025), (.32, .025)]]:
            g.tube('Ancient blue pictogram', [(x, y, .146) for x, y in outline], .009, 'blue')
        for s in (-1, 1):
            scroll(s * .14, s * .24, .09, .075, mirror=s)
    elif icon in ('item147', 'item148'):
        oval_body(.32, .43, 'orange' if icon == 'item147' else 'jade', beaded=True)
        bail(.5)
        if icon == 'item147':
            g.stone('Large diamond cut amber', (0, 0, .14), (.47, .47, .20), 'amber', 'square')
            for x, y in [(-.37, 0), (.37, 0), (0, -.44), (0, .44)]:
                g.stone('Cardinal diamond', (x, y, .1), (.13, .13, .08), 'amber', 'square')
    elif icon == '7item130':
        chain(rx=.095, ry=.45, cy=.85, count=30)
        bail(.39)
        g.tube('Eyeball suspension neck', [(0, .29, .36), (0, .34, .30), (0, .39, .12),
                (0, .40, .06)], .025, 'gold')
        g.ball('Round eyeball pendant', (0, 0, .21), (.30, .33, .29), 'sclera', 3)
        g.ball('Blue iris', (.045, -.05, .477), (.14, .14, .045), 'blue', 2)
        g.ball('Round pupil', (.045, -.05, .515), (.062, .062, .018), 'dark', 2)
        ring(0, .25, .18, .12, .36, .027)
        for x in (-.2, -.1, 0, .1, .2):
            g.tube('Gold eyeball retaining claws', [(x, .28, .35), (x * 1.1, .12, .42),
                   (x * 1.05, .04, .43)], .023, 'gold', True)
    elif icon == '7item131':
        oval_body(.34, .4, 'bronze', 'bronze')
        bail(.43, 'bronze')
        for x, y in [(-.14, .17), (.13, -.15), (.13, .18)]:
            scroll(x, y, .13, .15, 'gold')
        # A real side suspension ring, behind the medallion face.
        obj = ring(.43, .10, .15, .45, .02, .027, 'bronze')
        obj.rotation_euler.y = .55
    elif icon == '7item132':
        g.ball('Hand-shaped charm palm', (0, .05, .07), (.20, .25, .075), 'patina', 2)
        for i, x in enumerate((-.15, -.05, .05, .15)):
            length = [.33, .43, .47, .38][i]
            g.tube('Four distinct fingers', [(x, -.08, .07), (x, -.2, .06), (x, -.2 - length, .05)],
                   .035, 'patina')
            g.ball('Rounded fingertip', (x, -.2 - length, .05), (.035, .035, .035), 'patina', 1)
        g.tube('Single side thumb', [(-.13, .15, .07), (-.27, -.03, .07), (-.3, -.23, .05)], .045, 'patina')
        g.box('Wrist collar', (0, .32, .07), (.30, .14, .14), 'patina', .018)
        g.tube('Wrist suspension pin', [(0, .38, .07), (0, .45, .06)], .02, 'gold')
        ring(0, .03, .10, .12, .148, .016, 'gold')
        bail(.5, 'gold')
    elif icon == '7item133':
        oval_body(.43, .43, 'dark', 'silver')
        bail(.52, 'silver')
        skull_at(scale=1.5, red=True)
        for i in range(8):
            a = TAU * i / 8
            scroll(.29 * math.cos(a), .29 * math.sin(a), .075, .075, 'silver')
    elif icon == '7item134':
        ring(0, 0, .27, .27, .065, .028)
        ring(0, 0, .18, .18, .065, .014)
        for i in range(12):
            a = TAU * i / 12
            tangent = Vector((math.cos(a), math.sin(a), 0))
            side = Vector((-tangent.y, tangent.x, 0))
            outline = [tuple((tangent * r + side * s)[:2]) for r, s in ((.22, -.04), (.48, 0), (.23, .04))]
            g.plate('Twelve sun rays', outline, .035, .045, 'gold')
        g.plate('Eye-shaped frame', [(-.26, 0), (-.12, .12), (.12, .12), (.26, 0),
                (.12, -.12), (-.12, -.12)], .07, .05, 'gold')
        g.ball('Central eye', (0, 0, .13), (.09, .095, .045), 'bronze', 2)
        g.ball('Eye pupil', (0, 0, .169), (.029, .04, .012), 'dark', 1)
        bail(.55)
    elif icon == 'item149':
        skull_at(scale=1.0, metal='gold')
        for s in (-1, 1):
            for up in (-1, 1):
                outline = [(s * .08, up * .01), (s * .22, up * .08), (s * .32, up * .20),
                           (s * .34, up * .42), (s * .19, up * .57), (s * .24, up * .37),
                           (s * .12, up * .22), (s * .22, up * .23)]
                g.plate('Curved open bat-wing talisman', outline, .035, .075, 'gold')
    elif icon == 'item150':
        points = [(-.08, .47, .07), (-.28, .34, .07), (-.22, .14, .07), (.07, -.02, .07),
                  (.19, -.21, .07), (.03, -.45, .07), (-.19, -.4, .07), (-.21, -.23, .07)]
        g.tube('Silver paisley outer arm', points, .065, 'silver')
        g.tube('Silver paisley inner arm', [(.02, -.45, .07), (.29, -.22, .07), (.28, .1, .07),
               (.08, .25, .07), (.02, .09, .07), (.14, -.03, .07)], .052, 'silver')
        g.tube('Gold paisley inlay', [(x + .02, y, z + .05) for x, y, z in points], .018, 'gold')
        for i, (x, y) in enumerate([(-.08, .40), (-.22, .23), (.05, .13), (.18, -.08), (.04, -.32), (-.19, -.25)]):
            g.stone('Inset green cabochon', (x, y, .12), (.09, .10, .045), 'jade', 'pearl')
        bail(.55, 'silver', x=-.05)
    elif icon == 'item151':
        oval_body(.16, .28, 'purple', 'silver')
        for s in (-1, 1):
            for up in (-1, 1):
                outline = [(s * .10, up * .07), (s * .26, up * .10), (s * .42, up * .08),
                           (s * .29, up * .23), (s * .30, up * .39), (s * .23, up * .58),
                           (s * .16, up * .40), (s * .09, up * .29)]
                g.plate('Curved silver radial blade', outline, .03, .075, 'silver')
    else:
        raise ValueError(icon)


def finish(icon):
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        assert all(e.is_manifold for e in bm.edges), (icon, obj.name, 'open surface')
        assert all(f.calc_area() > 1e-10 for f in bm.faces), (icon, obj.name, 'degenerate')
        bm.to_mesh(obj.data)
        bm.free()
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = 'amulet_' + icon
    # Pack all parts together so a small link and a large pendant share texel density.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=.008)
    bpy.ops.object.mode_set(mode='OBJECT')
    lo = Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
    shift = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in obj.data.vertices:
        v.co -= shift
    obj.data.calc_loop_triangles()
    triangles = len(obj.data.loop_triangles)
    assert 100 < triangles < 15000, (icon, triangles)
    bpy.ops.wm.save_as_mainfile(filepath=str(P / f'work/blend/amulet_{icon}.blend'))
    out = P / f'work/finished/amulet_{icon}_export.glb'
    bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLB', use_selection=True, export_yup=True,
                              export_materials='EXPORT', export_cameras=False, export_animations=False)
    return {'icon': icon, 'triangles': triangles, 'route': 'Blender component modelling',
            'export': str(out.relative_to(P)), 'texture_source': 'Imagegen material painting',
            'canonical_design': GROUPS.get(icon, icon)}


def main():
    only = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else set()
    target = P / 'receipts/amulet_builds.json'
    records = json.loads(target.read_text()) if target.exists() else {}
    for row in json.loads((P / 'ownership.json').read_text()):
        icon = row['icon']
        if row['family'] != 'amulets' or (only and icon not in only):
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        MATERIALS.clear()
        make(GROUPS.get(icon, icon))
        records[icon] = finish(icon)
        target.write_text(json.dumps(records, indent=2) + '\n')
        print('BUILT', icon, records[icon]['triangles'], flush=True)


if __name__ == '__main__':
    main()
