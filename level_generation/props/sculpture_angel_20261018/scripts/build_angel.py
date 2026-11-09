"""Angel Statuette (7item263): a standing winged classical bronze figure on a two-tier stone plinth, built in Blender.

Image generation refused this nude statue twice, so nothing here uses generated images. A detailed source (skin-
modifier figure, head with hair bun, individually modelled wing feathers, bevelled plinth) is voxel-merged into one
solid, collapse-reduced to the triangle budget, cleaned of self-intersections by an exact self-union, unwrapped,
and baked from the detailed source: procedural patinated bronze and stone base colour, roughness and a tangent normal
map. The figure faces glTF +Z (Blender -Y), like the other statuettes; the plinth stands on the ground.

Usage: blender --background --python build_angel.py   -> work/angel_source.blend, work/angel_export.glb"""
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'level_generation/props/items_wip_equipment_geometry_finish/scripts'))
from repair_geometry import activate, apply  # noqa: E402
from resolve_self_intersections import intersecting_faces, separate_touching_folds  # noqa: E402

BUDGET = 3200
TEXTURE = 512
PLINTH_TOP = 0.13

# Skeleton: name -> (position, (radius across, radius front-to-back)); the figure faces -Y in contrapposto, weight
# on her right leg, left knee eased forward, left hand on the hip, right arm hanging, head turned up to her left.
JOINTS = {
    'pelvis': ((0.0, 0.0, 0.585), (0.085, 0.06)),
    'waist': ((0.0, -0.002, 0.67), (0.056, 0.042)),
    'chest': ((0.0, -0.006, 0.765), (0.068, 0.05)),
    'shoulders': ((0.0, 0.0, 0.84), (0.058, 0.042)),
    'neck': ((0.004, -0.004, 0.885), (0.024, 0.024)),
    'r_hip': ((0.05, 0.0, 0.56), (0.062, 0.06)),
    'r_knee': ((0.042, -0.006, 0.37), (0.035, 0.037)),
    'r_ankle': ((0.038, 0.008, 0.168), (0.021, 0.023)),
    'r_toe': ((0.042, -0.075, 0.142), (0.022, 0.013)),
    'l_hip': ((-0.05, 0.0, 0.565), (0.062, 0.06)),
    'l_knee': ((-0.06, -0.035, 0.375), (0.035, 0.037)),
    'l_ankle': ((-0.064, 0.014, 0.18), (0.021, 0.023)),
    'l_toe': ((-0.072, -0.06, 0.145), (0.022, 0.013)),
    'r_shoulder': ((0.092, 0.0, 0.832), (0.037, 0.036)),
    'r_elbow': ((0.122, 0.012, 0.69), (0.027, 0.027)),
    'r_wrist': ((0.132, -0.004, 0.566), (0.019, 0.017)),
    'r_hand': ((0.134, -0.01, 0.52), (0.021, 0.011)),
    'l_shoulder': ((-0.092, 0.0, 0.832), (0.037, 0.036)),
    'l_elbow': ((-0.17, 0.035, 0.72), (0.027, 0.027)),
    'l_wrist': ((-0.11, 0.0, 0.628), (0.019, 0.017)),
    'l_hand': ((-0.082, -0.014, 0.612), (0.021, 0.011)),
}
BONES = [('pelvis', 'waist'), ('waist', 'chest'), ('chest', 'shoulders'), ('shoulders', 'neck'),
         ('pelvis', 'r_hip'), ('r_hip', 'r_knee'), ('r_knee', 'r_ankle'), ('r_ankle', 'r_toe'),
         ('pelvis', 'l_hip'), ('l_hip', 'l_knee'), ('l_knee', 'l_ankle'), ('l_ankle', 'l_toe'),
         ('shoulders', 'r_shoulder'), ('r_shoulder', 'r_elbow'), ('r_elbow', 'r_wrist'), ('r_wrist', 'r_hand'),
         ('shoulders', 'l_shoulder'), ('l_shoulder', 'l_elbow'), ('l_elbow', 'l_wrist'), ('l_wrist', 'l_hand')]


def link(obj):
    bpy.context.collection.objects.link(obj)
    return obj


def mesh_object(name, vertices, faces):
    data = bpy.data.meshes.new(name)
    data.from_pydata([tuple(v) for v in vertices], [], faces)
    data.update()
    data.validate()
    return link(bpy.data.objects.new(name, data))


def figure():
    names = list(JOINTS)
    data = bpy.data.meshes.new('figure')
    data.from_pydata([JOINTS[n][0] for n in names], [(names.index(a), names.index(b)) for a, b in BONES], [])
    obj = link(bpy.data.objects.new('figure', data))
    skin = obj.modifiers.new('skin', 'SKIN')
    skin.use_smooth_shade = True
    for name, vertex in zip(names, obj.data.skin_vertices[0].data):
        vertex.radius = JOINTS[name][1]
        vertex.use_root = name == 'pelvis'
    subdivision = obj.modifiers.new('subdivision', 'SUBSURF')
    subdivision.levels = 2
    apply(obj, skin)
    apply(obj, subdivision)
    parts = [obj]
    # Head turned up and to her left, chin and nose, hair gathered into a bun.
    head = sphere('head', (0.012, -0.012, 0.95), (0.05, 0.058, 0.066))
    head.rotation_euler = (math.radians(-14), 0, math.radians(18))
    parts.append(head)
    parts.append(sphere('jaw', (0.016, -0.036, 0.922), (0.034, 0.036, 0.034)))
    parts.append(sphere('nose', (0.022, -0.07, 0.95), (0.009, 0.013, 0.016)))
    parts.append(sphere('bun', (-0.004, 0.048, 0.985), (0.034, 0.032, 0.03)))
    for side in (-1, 1):
        parts.append(sphere('breast', (0.036 * side, -0.05, 0.775), (0.034, 0.03, 0.032)))
        parts.append(sphere('buttock', (0.035 * side, 0.03, 0.57), (0.045, 0.035, 0.045)))
    return parts


def sphere(name, location, radii, segments=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=segments // 2, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = radii
    return obj


def blade(base, direction, side, length, width, thickness, rings=7):
    """A closed tapered feather: diamond cross-section, slightly cupped, rounded tip."""
    direction = direction.normalized()
    side = (side - direction * side.dot(direction)).normalized()
    normal = direction.cross(side).normalized()
    vertices, faces = [], []
    for i in range(rings):
        t = i / (rings - 1)
        w = width * (0.35 + 0.65 * math.sin(math.pi * min(1.0, 0.15 + 0.95 * t)) ** 0.6) * (1 - 0.55 * t ** 4)
        centre = base + direction * (length * t) + normal * (0.01 * math.sin(math.pi * t))
        h = thickness * (1 - 0.5 * t)
        vertices += [centre + side * w / 2, centre + normal * h / 2, centre - side * w / 2, centre - normal * h / 2]
    for i in range(rings - 1):
        for k in range(4):
            a, b = i * 4 + k, i * 4 + (k + 1) % 4
            faces.append((a, b, b + 4, a + 4))
    faces.append((3, 2, 1, 0))
    tip = len(vertices)
    vertices.append(base + direction * (length * 1.04))
    last = (rings - 1) * 4
    faces += [(last + k, last + (k + 1) % 4, tip) for k in range(4)]
    return vertices, faces


def wing(sign):
    """Wing swept back and up from the shoulder blade: a thick bone line of short blades, then broad overlapping
    feathers laid along it (each feather's width follows the bone, so neighbours overlap into one solid wing),
    secondaries hanging back near the body and primaries sweeping back and out at the tip, with a covert row."""
    root = Vector((0.03 * sign, 0.05, 0.8))
    wrist = Vector((0.15 * sign, 0.22, 0.99))
    hand = Vector((0.21 * sign, 0.34, 1.0))
    vertices, faces = [], []

    def add(part):
        offset = len(vertices)
        vertices.extend(part[0])
        faces.extend(tuple(i + offset for i in face) for face in part[1])

    arm = [root.lerp(wrist, t) if t <= 1 else wrist.lerp(hand, t - 1) for t in [i / 6 for i in range(13)]]
    for i in range(len(arm) - 1):
        add(blade(arm[i], arm[i + 1] - arm[i], Vector((0, 0, 1)), (arm[i + 1] - arm[i]).length * 1.5,
                  0.055 - 0.02 * i / len(arm), 0.034, rings=4))
    count = 20
    for i in range(count):
        t = i / (count - 1)
        position = t * (len(arm) - 1)
        k = min(len(arm) - 2, int(position))
        base = arm[k].lerp(arm[k + 1], position - k)
        tangent = arm[k + 1] - arm[k]
        down = Vector((0.0, 0.35, -1.0))
        out = Vector((sign * 0.45, 1.0, -0.5))
        direction = down.lerp(out, t ** 1.3)
        length = 0.2 + 0.16 * t ** 1.1
        add(blade(base, direction, tangent, length, 0.078 + 0.012 * t, 0.014))
        add(blade(base + Vector((0, -0.008, 0.004)), direction, tangent, length * 0.5, 0.07, 0.018, rings=5))
    return mesh_object(f'wing_{sign}', vertices, faces)


def plinth():
    parts = []
    for name, (size_x, size_y, z0, z1) in {'base': (0.42, 0.38, 0.0, 0.07), 'step': (0.34, 0.3, 0.07, PLINTH_TOP)}.items():
        bpy.ops.mesh.primitive_cube_add(location=(0, 0.005, (z0 + z1) / 2))
        obj = bpy.context.object
        obj.name = name
        obj.scale = (size_x / 2, size_y / 2, (z1 - z0) / 2)
        bpy.ops.object.transform_apply(scale=True)
        bevel = obj.modifiers.new('bevel', 'BEVEL')
        bevel.width = 0.008
        bevel.segments = 2
        apply(obj, bevel)
        parts.append(obj)
    return parts


def join(objects, name):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    return obj


def remesh(obj, size):
    obj.data.remesh_voxel_size = size
    activate(obj)
    bpy.ops.object.voxel_remesh()
    smooth = obj.modifiers.new('relax', 'SMOOTH')
    smooth.factor = 0.4
    smooth.iterations = 2
    apply(obj, smooth)


def material_source():
    """Procedural patinated bronze (metal) on the figure and wings, weathered stone on the plinth (by height)."""
    material = bpy.data.materials.new('angel_source')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes['Principled BSDF']
    geometry = nodes.new('ShaderNodeNewGeometry')
    position = nodes.new('ShaderNodeSeparateXYZ')
    links.new(geometry.outputs['Position'], position.inputs['Vector'])
    stone = nodes.new('ShaderNodeMath')
    stone.operation = 'LESS_THAN'
    stone.inputs[1].default_value = PLINTH_TOP + 0.004
    links.new(position.outputs['Z'], stone.inputs[0])
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 18.0
    noise.inputs['Detail'].default_value = 6.0
    fine = nodes.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 90.0
    # Worn raised edges show lighter bronze; recesses keep darker patina (pointiness, a Cycles bake input).
    pointiness = nodes.new('ShaderNodeMath')
    pointiness.operation = 'MULTIPLY_ADD'
    links.new(geometry.outputs['Pointiness'], pointiness.inputs[0])
    pointiness.inputs[1].default_value = 3.0
    pointiness.inputs[2].default_value = -1.0
    wear = nodes.new('ShaderNodeMath')
    wear.operation = 'ADD'
    wear.use_clamp = True
    links.new(pointiness.outputs[0], wear.inputs[0])
    scaled = nodes.new('ShaderNodeMath')
    scaled.operation = 'MULTIPLY'
    scaled.inputs[1].default_value = 0.45
    links.new(noise.outputs['Fac'], scaled.inputs[0])
    links.new(scaled.outputs[0], wear.inputs[1])
    bronze = nodes.new('ShaderNodeValToRGB')
    bronze.color_ramp.elements[0].position = 0.25
    bronze.color_ramp.elements[0].color = (0.2, 0.155, 0.09, 1)
    bronze.color_ramp.elements[1].position = 0.85
    bronze.color_ramp.elements[1].color = (0.5, 0.4, 0.25, 1)
    links.new(wear.outputs[0], bronze.inputs['Fac'])
    rock = nodes.new('ShaderNodeValToRGB')
    rock.color_ramp.elements[0].color = (0.06, 0.056, 0.04, 1)
    rock.color_ramp.elements[1].color = (0.16, 0.15, 0.11, 1)
    links.new(fine.outputs['Fac'], rock.inputs['Fac'])
    colour = nodes.new('ShaderNodeMix')
    colour.data_type = 'RGBA'
    links.new(stone.outputs[0], colour.inputs['Factor'])
    # Mottled patina: broad darker brown-olive patches over the bronze, with matching rougher surface.
    mottle = nodes.new('ShaderNodeTexNoise')
    mottle.inputs['Scale'].default_value = 7.0
    mottle.inputs['Detail'].default_value = 4.0
    patches = nodes.new('ShaderNodeValToRGB')
    patches.color_ramp.elements[0].position = 0.45
    patches.color_ramp.elements[1].position = 0.62
    links.new(mottle.outputs['Fac'], patches.inputs['Fac'])
    patina = nodes.new('ShaderNodeMix')
    patina.data_type = 'RGBA'
    patina.inputs['B'].default_value = (0.1, 0.09, 0.06, 1)
    patina_amount = nodes.new('ShaderNodeMath')
    patina_amount.operation = 'MULTIPLY'
    patina_amount.inputs[1].default_value = 0.75
    links.new(patches.outputs['Color'], patina_amount.inputs[0])
    links.new(patina_amount.outputs[0], patina.inputs['Factor'])
    links.new(bronze.outputs['Color'], patina.inputs['A'])
    links.new(patina.outputs['Result'], colour.inputs['A'])
    links.new(rock.outputs['Color'], colour.inputs['B'])
    links.new(colour.outputs['Result'], bsdf.inputs['Base Color'])
    rough = nodes.new('ShaderNodeMix')
    links.new(stone.outputs[0], rough.inputs['Factor'])
    bronze_rough = nodes.new('ShaderNodeMapRange')
    links.new(patches.outputs['Color'], bronze_rough.inputs['Value'])
    bronze_rough.inputs['To Min'].default_value = 0.34
    bronze_rough.inputs['To Max'].default_value = 0.62
    links.new(bronze_rough.outputs['Result'], rough.inputs['A'])
    rough.inputs['B'].default_value = 0.85
    links.new(rough.outputs['Result'], bsdf.inputs['Roughness'])
    # Surface relief for the normal bake: cast-bronze grain everywhere, pitted stone on the plinth, and fine
    # striations (feather barbs, hair strands) on the wings and head, selected by position.
    def math_node(operation, a, b, clamp=False):
        node = nodes.new('ShaderNodeMath')
        node.operation = operation
        node.use_clamp = clamp
        for index, value in enumerate((a, b)):
            if isinstance(value, float):
                node.inputs[index].default_value = value
            else:
                links.new(value, node.inputs[index])
        return node.outputs[0]

    absolute_x = math_node('ABSOLUTE', position.outputs['X'], 0.0)
    wings = math_node('MAXIMUM', math_node('GREATER_THAN', absolute_x, 0.14),
                      math_node('GREATER_THAN', position.outputs['Y'], 0.075))
    wings = math_node('MULTIPLY', wings, math_node('GREATER_THAN', position.outputs['Z'], 0.55))
    hair = math_node('GREATER_THAN', position.outputs['Z'], 0.955)
    striped = math_node('MAXIMUM', wings, hair)
    barbs = nodes.new('ShaderNodeTexWave')
    barbs.wave_type = 'BANDS'
    barbs.bands_direction = 'DIAGONAL'
    barbs.inputs['Scale'].default_value = 70.0
    barbs.inputs['Distortion'].default_value = 3.0
    barbs.inputs['Detail'].default_value = 2.0
    pits = nodes.new('ShaderNodeTexVoronoi')
    pits.feature = 'F1'
    pits.inputs['Scale'].default_value = 60.0
    grain = math_node('MULTIPLY', fine.outputs['Fac'], 0.6)
    height = math_node('ADD', grain, math_node('MULTIPLY', barbs.outputs['Fac'], striped))
    height = math_node('ADD', height, math_node('MULTIPLY', math_node('MULTIPLY', pits.outputs['Distance'], 1.5),
                                                stone.outputs[0]))
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.7
    bump.inputs['Distance'].default_value = 0.003
    links.new(height, bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    # Bronze figure and wings are metal, the plinth stone is not: carried only as the emission for the metallic
    # bake. The source shader itself stays dielectric, because Cycles bakes diffuse colour as albedo x (1 - metallic).
    metal = nodes.new('ShaderNodeMath')
    metal.operation = 'SUBTRACT'
    metal.inputs[0].default_value = 1.0
    links.new(stone.outputs[0], metal.inputs[1])
    links.new(metal.outputs[0], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 1.0
    return material


def bake(source, target):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.cage_extrusion = 0.012
    scene.render.bake.max_ray_distance = 0.03
    scene.render.bake.margin = 6
    images = {}
    material = bpy.data.materials.new('angel')
    material.use_nodes = True
    target.data.materials.clear()
    target.data.materials.append(material)
    nodes = material.node_tree.nodes
    for kind, colorspace in (('basecolor', 'sRGB'), ('occlusion', 'Non-Color'), ('roughness', 'Non-Color'),
                             ('metallic', 'Non-Color'), ('normal', 'Non-Color')):
        image = bpy.data.images.new(f'item_7item263_{kind}', TEXTURE, TEXTURE, alpha=False)
        image.colorspace_settings.name = colorspace
        node = nodes.new('ShaderNodeTexImage')
        node.image = image
        nodes.active = node
        bpy.ops.object.select_all(action='DESELECT')
        source.select_set(True)
        target.select_set(True)
        bpy.context.view_layer.objects.active = target
        if kind == 'basecolor':
            scene.render.bake.use_pass_direct = False
            scene.render.bake.use_pass_indirect = False
            scene.render.bake.use_pass_color = True
            bpy.ops.object.bake(type='DIFFUSE')
        elif kind == 'occlusion':
            scene.world = scene.world or bpy.data.worlds.new('bake_world')
            scene.world.light_settings.distance = 0.06
            bpy.ops.object.bake(type='AO')
        elif kind == 'roughness':
            bpy.ops.object.bake(type='ROUGHNESS')
        elif kind == 'metallic':
            bpy.ops.object.bake(type='EMIT')
        else:
            scene.render.bake.normal_space = 'TANGENT'
            bpy.ops.object.bake(type='NORMAL')
        images[kind] = (image, node)
    # Patina gathers in recesses: darken the base colour by the baked occlusion (between feathers, under the arms,
    # in the plinth steps), keeping open surfaces unchanged.
    colour = list(images['basecolor'][0].pixels)
    occlusion = list(images['occlusion'][0].pixels)
    for i in range(0, len(colour), 4):
        shade = 0.35 + 0.65 * min(1.0, occlusion[i] * 1.15)
        colour[i], colour[i + 1], colour[i + 2] = colour[i] * shade, colour[i + 1] * shade, colour[i + 2] * shade
    images['basecolor'][0].pixels = colour
    nodes.remove(images['occlusion'][1])
    # glTF metallic-roughness: G roughness, B metallic (binary: bronze 1, stone 0).
    pixels = list(images['roughness'][0].pixels)
    metallic = list(images['metallic'][0].pixels)
    mr = bpy.data.images.new('item_7item263_mr', TEXTURE, TEXTURE, alpha=False)
    mr.colorspace_settings.name = 'Non-Color'
    values = []
    for i in range(0, len(pixels), 4):
        values += [1.0, pixels[i], 1.0 if metallic[i] > 0.5 else 0.0, 1.0]
    mr.pixels = values
    links = material.node_tree.links
    bsdf = nodes['Principled BSDF']
    links.new(images['basecolor'][1].outputs['Color'], bsdf.inputs['Base Color'])
    mr_node = nodes.new('ShaderNodeTexImage')
    mr_node.image = mr
    separate = nodes.new('ShaderNodeSeparateColor')
    links.new(mr_node.outputs['Color'], separate.inputs['Color'])
    links.new(separate.outputs['Green'], bsdf.inputs['Roughness'])
    links.new(separate.outputs['Blue'], bsdf.inputs['Metallic'])
    normal_map = nodes.new('ShaderNodeNormalMap')
    links.new(images['normal'][1].outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
    nodes.remove(images['roughness'][1])
    nodes.remove(images['metallic'][1])
    material.use_backface_culling = True
    for image in (images['basecolor'][0], mr, images['normal'][0]):
        image.file_format = 'PNG'
        image.pack()


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    body = join(figure(), 'figure')
    wings = [wing(1), wing(-1)]
    pedestal = plinth()
    source = join([body] + wings + pedestal, 'angel_source')
    remesh(source, 0.0032)
    source.data.materials.append(material_source())
    for polygon in source.data.polygons:
        polygon.use_smooth = True
    # Game mesh: a copy collapsed to the budget, then crossings removed and touching folds separated.
    target = source.copy()
    target.data = source.data.copy()
    target.name = 'item_7item263'
    link(target)
    target.data.calc_loop_triangles()
    decimate = target.modifiers.new('budget', 'DECIMATE')
    decimate.ratio = (BUDGET - 300) / len(target.data.loop_triangles)
    decimate.use_collapse_triangulate = True
    apply(target, decimate)
    before = intersecting_faces(target)
    union = target.modifiers.new('resolve', 'BOOLEAN')
    union.operation = 'UNION'
    union.solver = 'EXACT'
    union.operand_type = 'COLLECTION'
    union.collection = bpy.data.collections.new('empty_operand')
    union.use_self = True
    apply(target, union)
    bm = bmesh.new()
    bm.from_mesh(target.data)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(2.0), verts=list(bm.verts), edges=list(bm.edges))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-7)
    bm.to_mesh(target.data)
    bm.free()
    touching = separate_touching_folds(target)
    bm = bmesh.new()
    bm.from_mesh(target.data)
    bad = [e for e in bm.edges if not e.is_manifold]
    assert not bad, ('non-manifold game mesh', len(bad))
    bm.free()
    after = intersecting_faces(target)
    activate(target)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.006)
    bpy.ops.object.mode_set(mode='OBJECT')
    for polygon in target.data.polygons:
        polygon.use_smooth = True
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    bake(source, target)
    # Ground the footprint at the origin; glTF export turns Blender -Y (her front) into +Z.
    low = Vector([min(v.co[i] for v in target.data.vertices) for i in range(3)])
    high = Vector([max(v.co[i] for v in target.data.vertices) for i in range(3)])
    shift = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    for vertex in target.data.vertices:
        vertex.co -= shift
    target.data.calc_loop_triangles()
    (HERE / 'work').mkdir(exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'work/angel_source.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.export_scene.gltf(filepath=str(HERE / 'work/angel_export.glb'), export_format='GLB',
                              use_selection=True, export_image_format='AUTO', export_yup=True)
    print('ANGEL', 'source faces', len(source.data.polygons), 'crossing faces after collapse', before, '->', after,
          'touching edges', touching, 'triangles', len(target.data.loop_triangles), 'size', list(high - low),
          flush=True)


if __name__ == '__main__':
    main()
