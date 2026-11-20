"""Shared Blender kit for the redone props: closed parts with named procedural materials, one joined mesh, a single
512 px bake (base colour, packed metallic/roughness, OpenGL tangent normal) and a grounded glTF export.

Materials are procedural: a base colour with gentle noise variation and cavity darkening (ambient occlusion), a
declared binary metalness and roughness, and a bump pattern (metal scratches, stone chips, wood grain, gem
smoothness). Every part is a closed solid; parts may interpenetrate but never leave open shells.
"""
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
TAU = math.tau
TEXTURE = 512

# name: (sRGB hex, metallic, roughness, bump kind, bump strength, colour variation)
PALETTE = {
    'gold': ('e0aa48', 1, .3, 'scratch', .25, .12),
    'brass': ('c49a52', 1, .38, 'scratch', .3, .16),
    'old_brass': ('9c7a3c', 1, .48, 'pitted', .45, .22),
    'copper': ('b8693d', 1, .42, 'pitted', .4, .2),
    'iron': ('5a5b5e', 1, .55, 'pitted', .5, .2),
    'rust': ('6b3a22', 0, .85, 'pitted', .7, .3),
    'silver': ('d0d3d8', 1, .3, 'scratch', .25, .08),
    'steel': ('a4a8ad', 1, .4, 'scratch', .4, .1),
    'wood': ('6e4426', 0, .65, 'grain', .5, .25),
    'violet_stone': ('3a1d74', 0, .38, 'chips', 1.2, .35),
    'moonstone': ('9fb8ea', 0, .1, 'smooth', .06, .45),
    'amethyst': ('7a35b5', 0, .1, 'smooth', .05, .12),
    'smoky_violet': ('5a4870', 0, .12, 'smooth', .05, .3),
    'diamond': ('e8f0ff', 0, .06, 'smooth', .03, .04),
    'turquoise': ('2fa69f', 0, .28, 'chips', .2, .2),
    'sapphire': ('1e3fae', 0, .1, 'smooth', .05, .12),
    'aquamarine': ('8fe0d0', 0, .1, 'smooth', .05, .12),
    'pearl': ('e6e0cc', 0, .25, 'smooth', .05, .06),
    'emerald': ('3b9a3c', 0, .1, 'smooth', .05, .12),
    'amber': ('d77d22', 0, .2, 'chips', .2, .2),
    'dark': ('26272b', 0, .6, 'pitted', .3, .1),
}
MATERIALS = {}


def linear(hex_colour):
    values = [int(hex_colour[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATERIALS.clear()


def material(name):
    if name in MATERIALS:
        return MATERIALS[name]
    colour, metal, rough, bump_kind, bump_strength, variation = PALETTE[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes['Principled BSDF']
    coords = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 9.0
    noise.inputs['Detail'].default_value = 5.0
    links.new(coords.outputs['Object'], noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    base = linear(colour)
    ramp.color_ramp.elements[0].color = (*[c * (1 - variation) for c in base], 1)
    ramp.color_ramp.elements[1].color = (*[min(1.0, c * (1 + variation)) for c in base], 1)
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    ao = nodes.new('ShaderNodeAmbientOcclusion')
    ao.inputs['Distance'].default_value = 0.06
    cavity = nodes.new('ShaderNodeMix')
    cavity.data_type = 'RGBA'
    cavity.blend_type = 'MULTIPLY'
    cavity.inputs['Factor'].default_value = 0.55
    links.new(ramp.outputs['Color'], cavity.inputs['A'])
    links.new(ao.outputs['AO'], cavity.inputs['B'])
    links.new(cavity.outputs['Result'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    # Metalness is carried in the emission for its own bake; the shader stays dielectric while baking because
    # Cycles bakes diffuse colour as albedo x (1 - metallic).
    bsdf.inputs['Emission Color'].default_value = (metal, metal, metal, 1)
    bsdf.inputs['Emission Strength'].default_value = 1.0
    height = pattern(nodes, links, coords, bump_kind)
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = bump_strength
    bump.inputs['Distance'].default_value = 0.004
    links.new(height, bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    mat['metal'] = metal
    MATERIALS[name] = mat
    return mat


def pattern(nodes, links, coords, kind):
    if kind == 'grain':
        wave = nodes.new('ShaderNodeTexWave')
        wave.wave_type = 'BANDS'
        wave.bands_direction = 'Y'
        wave.inputs['Scale'].default_value = 6.0
        wave.inputs['Distortion'].default_value = 8.0
        wave.inputs['Detail'].default_value = 4.0
        links.new(coords.outputs['Object'], wave.inputs['Vector'])
        return wave.outputs['Fac']
    if kind == 'chips':
        voronoi = nodes.new('ShaderNodeTexVoronoi')
        voronoi.feature = 'DISTANCE_TO_EDGE'
        voronoi.inputs['Scale'].default_value = 14.0
        links.new(coords.outputs['Object'], voronoi.inputs['Vector'])
        return voronoi.outputs['Distance']
    noise = nodes.new('ShaderNodeTexNoise')
    if kind == 'scratch':
        mapping = nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (60.0, 2.0, 60.0)
        links.new(coords.outputs['Object'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
        noise.inputs['Scale'].default_value = 4.0
    else:
        links.new(coords.outputs['Object'], noise.inputs['Vector'])
        noise.inputs['Scale'].default_value = {'pitted': 40.0, 'smooth': 6.0}.get(kind, 20.0)
    noise.inputs['Detail'].default_value = 8.0
    return noise.outputs['Fac']


def finish_part(obj, mat, smooth=True, angle=35):
    obj.data.materials.clear()
    obj.data.materials.append(material(mat))
    for polygon in obj.data.polygons:
        polygon.use_smooth = smooth
    return obj


def mesh(name, vertices, faces, mat, smooth=True):
    data = bpy.data.meshes.new(name)
    data.from_pydata([tuple(v) for v in vertices], [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    return finish_part(obj, mat, smooth)


def ball(name, position, radii, mat, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.scale = radii
    apply_transform(obj)
    return finish_part(obj, mat)


def uv_ball(name, position, radii, mat, segments=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.scale = radii
    apply_transform(obj)
    return finish_part(obj, mat)


def cabochon(name, position, radii, height, mat, segments=20, rings=5):
    """Domed stone with a flat base: a closed half-ellipsoid standing on z = position.z."""
    x0, y0, z0 = position
    vertices = [(x0, y0, z0 + height)]
    for r in range(1, rings + 1):
        phi = (math.pi / 2) * r / rings
        for i in range(segments):
            a = TAU * i / segments
            vertices.append((x0 + radii[0] * math.sin(phi) * math.cos(a), y0 + radii[1] * math.sin(phi) * math.sin(a),
                             z0 + height * math.cos(phi)))
    faces = [(0, 1 + (i + 1) % segments, 1 + i) for i in range(segments)]
    for r in range(rings - 1):
        for i in range(segments):
            a, b = 1 + r * segments + i, 1 + r * segments + (i + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    faces.append(tuple(1 + (rings - 1) * segments + i for i in range(segments)))
    return mesh(name, vertices, faces, mat)


def box(name, position, size, mat, bevel=0.0, segments=1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    apply_transform(obj)
    if bevel:
        modifier = obj.modifiers.new('bevel', 'BEVEL')
        modifier.width = bevel
        modifier.segments = segments
        apply_modifier(obj, modifier)
    return finish_part(obj, mat, smooth=False)


def ring(name, centre, radii, tube_radius, mat, segments=32, sides=8, z_scale=1.0):
    """Closed torus-like ring lying in the XY plane (elliptical path)."""
    cx, cy, cz = centre
    vertices = []
    for i in range(segments):
        a = TAU * i / segments
        ux, uy = math.cos(a), math.sin(a)
        for j in range(sides):
            b = TAU * j / sides
            r = tube_radius * math.cos(b)
            vertices.append((cx + (radii[0] + r) * ux, cy + (radii[1] + r) * uy,
                             cz + tube_radius * math.sin(b) * z_scale))
    faces = [(i * sides + j, i * sides + (j + 1) % sides, ((i + 1) % segments) * sides + (j + 1) % sides,
              ((i + 1) % segments) * sides + j) for i in range(segments) for j in range(sides)]
    return mesh(name, vertices, faces, mat)


def tube(name, points, radius, mat, sides=8, radii=None, caps=True):
    """Closed swept tube along points; radius per point via radii."""
    points = [Vector(p) for p in points]
    vertices = []
    previous = None
    for i, p in enumerate(points):
        tangent = (points[min(i + 1, len(points) - 1)] - points[max(0, i - 1)]).normalized()
        if previous is None:
            helper = Vector((0, 0, 1)) if abs(tangent.z) < .9 else Vector((1, 0, 0))
            normal = tangent.cross(helper).normalized()
        else:
            normal = (previous - tangent * previous.dot(tangent)).normalized()
        previous = normal
        other = tangent.cross(normal)
        r = radii[i] if radii else radius
        for j in range(sides):
            b = TAU * j / sides
            vertices.append(p + r * (normal * math.cos(b) + other * math.sin(b)))
    faces = [(i * sides + j, i * sides + (j + 1) % sides, (i + 1) * sides + (j + 1) % sides, (i + 1) * sides + j)
             for i in range(len(points) - 1) for j in range(sides)]
    if caps:
        faces += [tuple(reversed(range(sides))), tuple((len(points) - 1) * sides + j for j in range(sides))]
    return mesh(name, vertices, faces, mat)


def lathe(name, profile, mat, axis_points=None, segments=16):
    """Solid of revolution about the local Y axis: profile is [(y, radius)], closed at both ends."""
    vertices = []
    for y, r in profile:
        for i in range(segments):
            a = TAU * i / segments
            vertices.append((r * math.cos(a), y, r * math.sin(a)))
    n = len(profile)
    faces = [(k * segments + i, k * segments + (i + 1) % segments, (k + 1) * segments + (i + 1) % segments,
              (k + 1) * segments + i) for k in range(n - 1) for i in range(segments)]
    faces += [tuple(reversed(range(segments))), tuple((n - 1) * segments + i for i in range(segments))]
    return mesh(name, vertices, faces, mat)


def slab(name, outline, z0, z1, mat, bevel=0.0, segments=2, smooth=False):
    """Extruded closed polygon outline (counter-clockwise, XY) between z0 and z1, optionally bevelled."""
    count = len(outline)
    vertices = [(x, y, z) for z in (z0, z1) for x, y in outline]
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    faces += [(i, (i + 1) % count, (i + 1) % count + count, i + count) for i in range(count)]
    obj = mesh(name, vertices, faces, mat, smooth)
    if bevel:
        modifier = obj.modifiers.new('bevel', 'BEVEL')
        modifier.width = bevel
        modifier.segments = segments
        modifier.limit_method = 'ANGLE'
        apply_modifier(obj, modifier)
    return finish_part(obj, mat, smooth)


def faceted_stone(name, position, size, mat, sides=8, rotation=0.0):
    """Brilliant-like stone: pavilion point under the girdle, crown and table above (closed)."""
    x0, y0, z0 = position
    levels = [(.18, 0.0), (1.0, .38), (1.0, .46), (.72, .8), (.5, 1.0)]
    vertices = []
    for level, (radius, height) in enumerate(levels):
        for i in range(sides):
            a = TAU * (i + (.5 if level == 3 else 0)) / sides + rotation
            vertices.append((x0 + math.cos(a) * radius * size[0] / 2, y0 + math.sin(a) * radius * size[1] / 2,
                             z0 + height * size[2]))
    faces = [tuple(reversed(range(sides))), tuple(range(4 * sides, 5 * sides))]
    for level in range(4):
        for i in range(sides):
            j = (i + 1) % sides
            faces.append((level * sides + i, level * sides + j, (level + 1) * sides + j, (level + 1) * sides + i))
    obj = mesh(name, vertices, faces, mat, smooth=False)
    return obj


def apply_transform(obj):
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj,
                                   selected_editable_objects=[obj]):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def apply_modifier(obj, modifier):
    with bpy.context.temp_override(active_object=obj, object=obj):
        bpy.ops.object.modifier_apply(modifier=modifier.name)


def rotate(obj, degrees, axis='Z', pivot=(0, 0, 0)):
    from mathutils import Matrix
    matrix = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(degrees), 4, axis) @ Matrix.Translation(
        [-c for c in pivot])
    obj.data.transform(matrix)
    obj.data.update()
    return obj


def join(objects, name):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    return obj


def ground(obj):
    low = Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)])
    high = Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
    shift = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    for vertex in obj.data.vertices:
        vertex.co -= shift
    obj.data.update()
    return high - low


def bake_and_export(obj, icon, smooth_angle=35):
    """Unwrap, bake the procedural part materials into one 512 px PBR set and export work/<icon>_export.glb."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-7)
    bm.to_mesh(obj.data)
    bm.free()
    ground(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.008)
    bpy.ops.object.mode_set(mode='OBJECT')
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(smooth_angle))
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.render.bake.margin = 6
    scene.render.bake.use_selected_to_active = False
    world = bpy.data.worlds.new('bake_world')
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
    images = {}
    part_materials = [slot.material for slot in obj.material_slots]
    for kind, colorspace, bake_type in (('basecolor', 'sRGB', 'DIFFUSE'), ('roughness', 'Non-Color', 'ROUGHNESS'),
                                        ('metallic', 'Non-Color', 'EMIT'), ('normal', 'Non-Color', 'NORMAL')):
        image = bpy.data.images.new(f'item_{icon}_{kind}', TEXTURE, TEXTURE, alpha=False)
        image.colorspace_settings.name = colorspace
        for mat in part_materials:
            nodes = mat.node_tree.nodes
            node = nodes.get('bake_target') or nodes.new('ShaderNodeTexImage')
            node.name = 'bake_target'
            node.image = image
            nodes.active = node
        if kind == 'basecolor':
            scene.render.bake.use_pass_direct = False
            scene.render.bake.use_pass_indirect = False
            scene.render.bake.use_pass_color = True
        if kind == 'normal':
            scene.render.bake.normal_space = 'TANGENT'
        bpy.ops.object.bake(type=bake_type)
        images[kind] = image
    rough = list(images['roughness'].pixels)
    metal = list(images['metallic'].pixels)
    mr = bpy.data.images.new(f'item_{icon}_mr', TEXTURE, TEXTURE, alpha=False)
    mr.colorspace_settings.name = 'Non-Color'
    values = []
    for i in range(0, len(rough), 4):
        values += [1.0, rough[i], 1.0 if metal[i] > 0.5 else 0.0, 1.0]
    mr.pixels = values
    final = bpy.data.materials.new(f'item_{icon}')
    final.use_nodes = True
    final.use_backface_culling = True
    nodes, links = final.node_tree.nodes, final.node_tree.links
    bsdf = nodes['Principled BSDF']
    colour_node = nodes.new('ShaderNodeTexImage')
    colour_node.image = images['basecolor']
    links.new(colour_node.outputs['Color'], bsdf.inputs['Base Color'])
    mr_node = nodes.new('ShaderNodeTexImage')
    mr_node.image = mr
    separate = nodes.new('ShaderNodeSeparateColor')
    links.new(mr_node.outputs['Color'], separate.inputs['Color'])
    links.new(separate.outputs['Green'], bsdf.inputs['Roughness'])
    links.new(separate.outputs['Blue'], bsdf.inputs['Metallic'])
    normal_node = nodes.new('ShaderNodeTexImage')
    normal_node.image = images['normal']
    normal_map = nodes.new('ShaderNodeNormalMap')
    links.new(normal_node.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
    obj.data.materials.clear()
    obj.data.materials.append(final)
    for polygon in obj.data.polygons:
        polygon.material_index = 0
    for image in (images['basecolor'], mr, images['normal']):
        image.file_format = 'PNG'
        image.pack()
    obj.name = f'item_{icon}'
    obj.data.calc_loop_triangles()
    work = PROJECT / 'work'
    work.mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(work / f'{icon}.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(work / f'{icon}_export.glb'), export_format='GLB', use_selection=True,
                              export_image_format='AUTO', export_yup=True)
    low = Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)])
    high = Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
    print('EXPORTED', icon, 'triangles', len(obj.data.loop_triangles), 'size', [round(v, 4) for v in high - low],
          flush=True)
