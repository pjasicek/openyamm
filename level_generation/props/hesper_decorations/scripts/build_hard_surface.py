"""Build the hard-surface Hesper decorations in Blender and export one GLB each to work/hard_surface/.

    blender --background --factory-startup --python scripts/build_hard_surface.py [-- <name> ...]

Geometry is built from primitives in metres (1 m = 100 world units; the binding's `height` sets the game size).
Textures are the Hesper sets in design/kreegan_world/art (textures_d0/blv, textures_out1/masters,
textures_interiors/masters), cube-projected at the same density as the BLV and BModel faces: one native texel (a
quarter of a master pixel) per world unit, so a 128 x 256 wall panel repeats every 1.28 x 2.56 m. Small gold parts and
beams use strips cut from a band of a wall texture and mirrored so they tile (`STRIPS`, work/hard_surface/derived/):
`hcgold` from `hctrim`'s gold band, `hcbeam` from `hcgirder`'s horizontal beam. Each material
gets its base colour, a tangent normal map derived from the texture's fine luminance detail
(work/hard_surface/normals/), and its own roughness and metallic; glowing parts (lamp glass, the casket's seam, candle flames) add a constant
emissive colour, which the engine reads as glTF emissiveFactor.
"""
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ART = os.path.join(REPO, 'design', 'kreegan_world', 'art')
OUT = os.path.join(HERE, 'work', 'hard_surface')
NORMALS = os.path.join(OUT, 'normals')
DERIVED = os.path.join(OUT, 'derived')
TEXTURES = {
    **{name: os.path.join(ART, 'textures_d0', 'blv', name + '.png')
       for name in ['hcpanel', 'hcrecess', 'hctrim', 'hcgirder', 'hcsign', 'hcconsole', 'hcrate', 'hcontainer',
                    'hlglass', 'hlhull', 'hlhulltorn', 'hcfloor', 'hchazard']},
    **{name: os.path.join(ART, 'textures_out1', 'masters', name + '.png')
       for name in ['hoterm', 'hopylon', 'hosalvage', 'hoscrap', 'hoaresin', 'hochitin', 'hoplate', 'hotarp',
                    'hhprefab']},
    **{name: os.path.join(ART, 'textures_interiors', 'masters', name + '.png')
       for name in ['hfcloth', 'hfplank', 'hfrug', 'hamarble', 'higlass', 'hccrate', 'hfawning', 'hfbanrd',
                    'hawater']},
    'hcstripw': os.path.join(ART, 'textures_d0', 'blv', 'hcstripw.png'),
    'hcgold': os.path.join(DERIVED, 'hcgold.png'),
    'hcbeam': os.path.join(DERIVED, 'hcbeam.png'),
    'hckeypad': os.path.join(DERIVED, 'hckeypad.png'),
}
# Strip: source texture and the master rows of its band (top row 0).
STRIPS = {'hcgold': ('hctrim', 4, 44), 'hcbeam': ('hcgirder', 222, 298)}
# Material: texture, roughness, metallic, normal strength.
MATERIALS = {
    'ceramic': ('hoterm', 0.65, 0.0, 1.0), 'pylon': ('hopylon', 0.6, 0.0, 1.0), 'trim': ('hcgold', 0.35, 0.85, 1.2),
    'girder': ('hcbeam', 0.55, 0.3, 1.4), 'sign': ('hcsign', 0.45, 0.0, 0.8), 'console': ('hcconsole', 0.4, 0.1, 0.8),
    'crate': ('hcrate', 0.6, 0.0, 1.0), 'container': ('hcontainer', 0.6, 0.0, 1.0), 'glass': ('hlglass', 0.12, 0.0, 0.6),
    'hull': ('hlhull', 0.6, 0.0, 1.0), 'hull_torn': ('hlhulltorn', 0.7, 0.1, 1.6), 'plate': ('hoplate', 0.7, 0.0, 1.2),
    'salvage': ('hosalvage', 0.75, 0.45, 1.5), 'scrap': ('hoscrap', 0.8, 0.4, 1.5), 'resin': ('hoaresin', 0.3, 0.0, 1.2),
    'chitin': ('hochitin', 0.35, 0.0, 1.4), 'tarp': ('hotarp', 0.9, 0.0, 1.0), 'hazard': ('hchazard', 0.6, 0.0, 1.0),
    'panel': ('hcpanel', 0.6, 0.0, 1.0), 'cloth': ('hfcloth', 0.95, 0.0, 1.2), 'rug': ('hfrug', 0.95, 0.0, 1.2),
    'plank': ('hfplank', 0.85, 0.0, 1.3), 'marble': ('hamarble', 0.3, 0.0, 0.6), 'wax': ('hamarble', 0.6, 0.0, 0.3),
    'glass_blue': ('higlass', 0.12, 0.0, 0.6), 'keypad': ('hckeypad', 0.2, 0.0, 0.4),
    'colony_crate': ('hccrate', 0.55, 0.0, 1.0), 'awning': ('hfawning', 0.9, 0.0, 1.0),
    'prefab': ('hhprefab', 0.6, 0.1, 1.0), 'banner': ('hfbanrd', 0.9, 0.0, 0.8),
    # Glowing: texture, roughness, metallic, normal strength, emissive colour.
    'lamp': ('hcstripw', 0.3, 0.0, 0.3, (1.0, 0.72, 0.35)), 'seam': ('hcstripw', 0.3, 0.0, 0.3, (0.35, 0.85, 1.0)),
    'flame': ('hcstripw', 0.5, 0.0, 0.0, (1.0, 0.55, 0.15)),
    'energy': ('hcstripw', 0.2, 0.0, 0.0, (0.75, 0.9, 1.0)), 'cell': ('hcstripw', 0.2, 0.0, 0.0, (0.35, 0.8, 1.0)),
    # The light fixtures' diffusers: the colony's cool work light and the emergency amber (LIGHTING in
    # design/kreegan_world/DUNGEON_PLAYBOOK.md); an unlit diffuser is plain frosted glass.
    'diffuser_white': ('hcstripw', 0.25, 0.0, 0.0, (0.88, 0.93, 1.0)),
    'diffuser_amber': ('hcstripw', 0.3, 0.0, 0.0, (1.0, 0.6, 0.24)),
    'diffuser_off': ('hlglass', 0.3, 0.0, 0.4),
    'lamp_red': ('hcstripw', 0.3, 0.0, 0.0, (1.0, 0.18, 0.12)),
    'lamp_green': ('hcstripw', 0.3, 0.0, 0.0, (0.3, 1.0, 0.4)),
    'water': ('flat_46_88_104', 0.05, 0.0, 0.0),
    # The stat barrels' liquids (MM7's barrel colours, each a +2 stat), glowing a little; empty, a dark stain.
    **{'liquid_' + colour: ('flat_' + '_'.join(str(int(c * 255)) for c in rgb), 0.1, 0.0, 0.0,
                            tuple(c * 0.45 for c in rgb)) for colour, rgb in {
        'red': (0.85, 0.1, 0.08), 'orange': (0.95, 0.45, 0.08), 'blue': (0.12, 0.3, 0.95),
        'yellow': (0.95, 0.85, 0.15), 'green': (0.15, 0.8, 0.2), 'purple': (0.55, 0.15, 0.85),
        'white': (0.9, 0.92, 0.95)}.items()},
    'liquid_empty': ('flat_34_30_28', 0.7, 0.0, 0.0),
}


def strip(name):
    """A band of a wall texture, mirrored below itself so it tiles vertically."""
    path = TEXTURES[name]
    if not os.path.exists(path):
        source, top, bottom = STRIPS[name]
        os.makedirs(DERIVED, exist_ok=True)
        image = bpy.data.images.load(TEXTURES[source])
        w, h = image.size
        pixels = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]    # top row first
        band = pixels[top:bottom]
        tiled = np.concatenate([band, band[::-1]], 0)[::-1]                         # back to Blender's bottom-up
        out = bpy.data.images.new(name, w, tiled.shape[0])
        out.pixels[:] = tiled.ravel()
        out.filepath_raw = path
        out.file_format = 'PNG'
        out.save()
        bpy.data.images.remove(image)
    return path


def keypad_texture():
    """The colonial locker's keypad, drawn: a dark glass plate in a gold frame, a 3 x 4 grid of pale keys and a
    blue status bar across the top. Mapped once over the panel's face (`fit_front`)."""
    path = TEXTURES['hckeypad']
    if os.path.exists(path):
        return path
    os.makedirs(DERIVED, exist_ok=True)
    w, h = 256, 192
    y, x = np.mgrid[0:h, 0:w]
    rgb = np.zeros((h, w, 3), np.float32) + (0.05, 0.06, 0.08)
    frame = (x < 10) | (x >= w - 10) | (y < 10) | (y >= h - 10)
    rgb[frame] = (0.62, 0.47, 0.24)
    bar = (y >= 20) & (y < 40) & (x >= 24) & (x < w - 24)
    rgb[bar] = (0.25, 0.65, 1.0)
    for row in range(4):
        for column in range(3):
            x0, y0 = 70 + column * 42, 52 + row * 33
            key = (x >= x0) & (x < x0 + 32) & (y >= y0) & (y < y0 + 25)
            rgb[key] = (0.55, 0.58, 0.6)
            rgb[key & ((x == x0) | (y == y0))] = (0.75, 0.78, 0.8)
    image = bpy.data.images.new('hckeypad', w, h)
    image.pixels[:] = np.concatenate([rgb[::-1], np.ones((h, w, 1), np.float32)], -1).ravel()
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    bpy.data.images.remove(image)
    return path


def flat_texture(name):
    """One plain colour (flat_<r>_<g>_<b>, 0-255) as a small texture: liquids and water."""
    path = os.path.join(DERIVED, name + '.png')
    TEXTURES[name] = path
    if not os.path.exists(path):
        os.makedirs(DERIVED, exist_ok=True)
        rgb = [int(v) / 255 for v in name.split('_')[1:]]
        image = bpy.data.images.new(name, 16, 16)
        image.pixels = [c for _ in range(16 * 16) for c in (*rgb, 1.0)]
        image.filepath_raw = path
        image.file_format = 'PNG'
        image.save()


def derived_normal(texture, strength):
    """A tangent-space normal map (OpenGL) from the texture's high-pass luminance."""
    os.makedirs(NORMALS, exist_ok=True)
    path = os.path.join(NORMALS, f'{texture}_n{strength:g}.png')
    if os.path.exists(path):
        return path
    image = bpy.data.images.load(TEXTURES[texture])
    w, h = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)
    lum = pixels[..., :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    blur = lum.copy()
    for _ in range(6):
        blur = (np.roll(blur, 1, 0) + np.roll(blur, -1, 0) + np.roll(blur, 1, 1) + np.roll(blur, -1, 1) + blur) / 5
    height = lum - blur * 0.5
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * strength * 4
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * strength * 4
    n = np.stack([-dx, -dy, np.ones_like(dx)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    out = np.concatenate([n * 0.5 + 0.5, np.ones((h, w, 1), np.float32)], -1)
    normal = bpy.data.images.new(os.path.basename(path), w, h)
    normal.pixels[:] = out.ravel()
    normal.filepath_raw = path
    normal.file_format = 'PNG'
    normal.save()
    bpy.data.images.remove(image)
    return path


def material(key):
    existing = bpy.data.materials.get('HS_' + key)
    if existing:
        return existing
    texture, rough, metal, nstrength = MATERIALS[key][:4]
    if texture in STRIPS:
        strip(texture)
    if texture == 'hckeypad':
        keypad_texture()
    if texture.startswith('flat_'):
        flat_texture(texture)
    mat = bpy.data.materials.new('HS_' + key)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes['Principled BSDF']
    base = nodes.new('ShaderNodeTexImage')
    base.image = bpy.data.images.load(TEXTURES[texture], check_existing=True)
    links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
    normal_tex = nodes.new('ShaderNodeTexImage')
    normal_tex.image = bpy.data.images.load(derived_normal(texture, nstrength), check_existing=True)
    normal_tex.image.colorspace_settings.name = 'Non-Color'
    normal_map = nodes.new('ShaderNodeNormalMap')
    links.new(normal_tex.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if len(MATERIALS[key]) > 4:
        bsdf.inputs['Emission Color'].default_value = (*MATERIALS[key][4], 1.0)
        # An optional sixth value: the strength (glTF KHR_materials_emissive_strength), for glows past 1.
        bsdf.inputs['Emission Strength'].default_value = MATERIALS[key][5] if len(MATERIALS[key]) > 5 else 1.0
    return mat


def finish(obj, key):
    """Cube-project UVs at the shared density (one native texel per world unit) and assign the material."""
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=1.0, correct_aspect=False, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    mat = material(key)
    width, height = mat.node_tree.nodes['Image Texture'].image.size
    repeat_u, repeat_v = width / 4 / 100, height / 4 / 100          # metres per repeat: native texels / 100
    for loop in obj.data.uv_layers.active.data:
        loop.uv = (loop.uv.x / repeat_u, loop.uv.y / repeat_v)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    bpy.ops.object.shade_flat()
    return obj


def fit_front(obj):
    """Map the texture once over the object's x-z extent (seen from the front, -y): a panel's face shows it whole."""
    xs = [v.co.x for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    for loop in obj.data.loops:
        co = obj.data.vertices[loop.vertex_index].co
        obj.data.uv_layers.active.data[loop.index].uv = ((co.x - min(xs)) / (max(xs) - min(xs)),
                                                         (co.z - min(zs)) / (max(zs) - min(zs)))
    return obj


def cylinder(radius, depth, location, key, vertices=16, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location,
                                        rotation=rotation)
    return finish(bpy.context.active_object, key)


def lathe(profile, location, key, sides=24, rotation=(0, 0, 0), crease=30.0):
    """A smooth-shaded solid of revolution about its local z: `profile` is (radius, z) from bottom to top, metres; an
    end with a radius closes with a flat cap. Smooth normals around the circumference; hard edges only at the caps
    and where the profile turns by more than `crease` degrees (a drum meeting its cone ends). UVs at the shared
    density (`finish`): around the circumference by arc length (u) and along the profile by slant length (v), one
    wrap seam on the side facing down (or the back, +y, for an upright part); caps planar. Used where flat-shaded
    `cylinder`s read as polygons close up (the turrets, user review 2026-10-22)."""
    mat = material(key)
    width, height = mat.node_tree.nodes['Image Texture'].image.size
    repeat_u, repeat_v = width / 4 / 100, height / 4 / 100
    turn = Euler(rotation).to_matrix()
    seam = turn.inverted() @ Vector((0, 0, -1))
    if seam.xy.length < 0.5:
        seam = turn.inverted() @ Vector((0, 1, 0))
    start = math.atan2(seam.y, seam.x)
    angles = [start + 2 * math.pi * i / sides for i in range(sides + 1)]       # the last column repeats the first
    slant = [0.0]
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        slant.append(slant[-1] + math.hypot(r1 - r0, z1 - z0))
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    rings = [[bm.verts.new((math.cos(a) * r, math.sin(a) * r, z)) for a in angles[:-1]] for r, z in profile]
    sides_faces = []
    for k in range(len(profile) - 1):
        row = []
        for i in range(sides):
            j = (i + 1) % sides
            face = bm.faces.new([rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]])
            for loop, (column, level) in zip(face.loops, ((i, k), (i + 1, k), (i + 1, k + 1), (i, k + 1))):
                loop[uv].uv = (angles[column] * profile[level][0] / repeat_u, slant[level] / repeat_v)
            face.smooth = True
            row.append(face)
        sides_faces.append(row)
    for k, (r, z) in enumerate(profile):
        if r > 0 and k in (0, len(profile) - 1):              # strip-triangulated: no n-gon, no many-spoke vertex
            ring = rings[k] if k else list(reversed(rings[k]))
            zigzag = [ring[(i + 1) // 2] if i % 2 else ring[-(i // 2)] for i in range(sides)]
            for t in range(sides - 2):
                a, b, c = zigzag[t], zigzag[t + 1], zigzag[t + 2]
                face = bm.faces.new((a, c, b) if t % 2 else (a, b, c))
                for loop in face.loops:
                    loop[uv].uv = (loop.vert.co.x / repeat_u, loop.vert.co.y / repeat_v)
                face.smooth = True                            # flat: its rim edges are hard
            for i in range(sides):
                bm.edges.get([ring[i], ring[(i + 1) % sides]]).smooth = False
    bmesh.ops.triangulate(bm, faces=[f for row in sides_faces for f in row], quad_method='SHORT_EDGE')
    bm.normal_update()
    for k in range(1, len(profile) - 1):                                       # creases between profile segments
        (r0, z0), (r1, z1), (r2, z2) = profile[k - 1:k + 2]
        if Vector((r1 - r0, z1 - z0)).angle(Vector((r2 - r1, z2 - z1)), 0.0) > math.radians(crease):
            for i in range(sides):
                bm.edges.get([rings[k][i], rings[k][(i + 1) % sides]]).smooth = False
    mesh = bpy.data.meshes.new('lathe')
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new('lathe', mesh)
    obj.location, obj.rotation_euler = location, rotation
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    mesh.materials.append(mat)
    return obj


def round_cylinder(radius, depth, location, key, sides=16, rotation=(0, 0, 0)):
    """A smooth-shaded closed cylinder (`lathe`): `cylinder`'s size and placement, round close up."""
    return lathe([(radius, -depth / 2), (radius, depth / 2)], location, key, sides, rotation)


def cube(size, location, key, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.scale = size
    return finish(obj, key)


def faceted_rock(radius, location, key, seed, stretch=(1, 1, 1), subdivisions=1):
    rng = random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=radius, location=location)
    obj = bpy.context.active_object
    for v in obj.data.vertices:
        v.co *= 0.75 + rng.random() * 0.5
        v.co.x *= stretch[0]
        v.co.y *= stretch[1]
        v.co.z *= stretch[2]
    return finish(obj, key)


def shard(height, base, location, key, seed, lean=0.0):
    rng = random.Random(seed)
    bm = bmesh.new()
    sides = 5
    ring = [bm.verts.new((math.cos(a) * base * (0.7 + rng.random() * 0.6), math.sin(a) * base * (0.7 + rng.random() * 0.6),
                          0)) for a in [i * 2 * math.pi / sides for i in range(sides)]]
    tip = bm.verts.new((lean * height, rng.uniform(-0.1, 0.1) * height, height))
    for i in range(sides):
        bm.faces.new([ring[i], ring[(i + 1) % sides], tip])
    bm.faces.new(list(reversed(ring)))
    mesh = bpy.data.meshes.new('shard')
    bm.to_mesh(mesh)
    obj = bpy.data.objects.new('shard', mesh)
    obj.location = location
    obj.rotation_euler = (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), rng.uniform(0, math.pi))
    bpy.context.collection.objects.link(obj)
    return finish(obj, key)


def cone(radius1, radius2, depth, location, key, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth,
                                    location=location, rotation=rotation)
    return finish(bpy.context.active_object, key)


def bipyramid(radius, height, location, key, sides=6, rotation=(0, 0, 0)):
    """A crystal: a ring of points between two tips."""
    bm = bmesh.new()
    ring = [bm.verts.new((math.cos(i * 2 * math.pi / sides) * radius, math.sin(i * 2 * math.pi / sides) * radius, 0))
            for i in range(sides)]
    top, bottom = bm.verts.new((0, 0, height * 0.6)), bm.verts.new((0, 0, -height * 0.4))
    for i in range(sides):
        bm.faces.new([ring[i], ring[(i + 1) % sides], top])
        bm.faces.new([ring[(i + 1) % sides], ring[i], bottom])
    mesh = bpy.data.meshes.new('crystal')
    bm.to_mesh(mesh)
    obj = bpy.data.objects.new('crystal', mesh)
    obj.location = location
    obj.rotation_euler = rotation
    bpy.context.collection.objects.link(obj)
    return finish(obj, key)


def join(objects):
    for other in bpy.context.selected_objects:
        other.select_set(False)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects) > 1:
        bpy.ops.object.join()
    return bpy.context.active_object


def assemble(parts, location, rotation=(0, 0, 0)):
    """Build a sub-assembly at the origin with parts(), join it and move it into place."""
    before = set(bpy.context.scene.objects)
    parts()
    obj = join([o for o in bpy.context.scene.objects if o not in before])
    obj.location = location
    obj.rotation_euler = rotation
    return obj


# --- The models -------------------------------------------------------------------------------------------------------
def pylon():
    cylinder(0.32, 0.3, (0, 0, 0.15), 'plate', 12)
    cylinder(0.14, 3.0, (0, 0, 1.8), 'pylon', 12)
    cylinder(0.2, 0.12, (0, 0, 3.3), 'trim', 12)
    cylinder(0.12, 0.18, (0, 0, 3.45), 'glass', 12)


def container():
    cube((2.4, 1.2, 1.25), (0, 0, 0.625), 'container')
    for x in (-1.16, 1.16):                         # the end bands stand proud of the ends, not flush with them
        cube((0.1, 1.24, 1.29), (x, 0, 0.645), 'trim')


def fuel_tank():
    cylinder(0.62, 2.6, (0, 0, 0.8), 'ceramic', 20, rotation=(0, math.pi / 2, 0))
    for x in (-1.3, 1.3):
        cylinder(0.5, 0.12, (x, 0, 0.8), 'trim', 20, rotation=(0, math.pi / 2, 0))
    for x in (-0.8, 0.8):
        cube((0.18, 1.0, 0.3), (x, 0, 0.15), 'plate')


def gantry_segment():
    length, w = 4.5, 0.7
    for y in (-w / 2, w / 2):
        for z in (0.12, 0.12 + w):
            cube((length, 0.12, 0.12), (0, y, z), 'girder')
    for i in range(6):
        x = -length / 2 + 0.1 + i * (length - 0.2) / 5
        cube((0.1, w, 0.1), (x, 0, 0.12 + w), 'girder')
        cube((0.1, 0.1, w), (x, -w / 2, 0.12 + w / 2), 'girder')
        cube((0.1, 0.1, w), (x, w / 2, 0.12 + w / 2), 'girder')
    bpy.ops.object.select_all(action='SELECT')
    for obj in bpy.context.selected_objects:
        obj.rotation_euler = (0.12, 0.05, 0)


def signpost():
    cylinder(0.08, 2.1, (0, 0, 1.05), 'pylon', 10)
    cube((0.9, 0.06, 0.5), (0.35, 0, 1.75), 'sign', rotation=(0, -0.08, 0.15))
    cube((0.7, 0.06, 0.4), (-0.25, 0.05, 1.25), 'sign', rotation=(0, 0.06, -0.6))


def tablet_plinth():
    cube((0.9, 0.9, 0.25), (0, 0, 0.125), 'plate')
    cube((0.7, 0.7, 0.2), (0, 0, 0.35), 'plate')
    cube((0.55, 0.12, 0.9), (0, 0, 0.9), 'glass', rotation=(0.08, 0, 0))
    cube((0.62, 0.18, 0.08), (0, 0, 0.47), 'trim')


def brazier():
    cylinder(0.32, 0.75, (0, 0, 0.375), 'salvage', 14)
    cylinder(0.29, 0.06, (0, 0, 0.735), 'resin', 14)              # the coals stand above the rim
    for i in range(3):
        a = i * 2 * math.pi / 3
        cube((0.06, 0.06, 0.3), (math.cos(a) * 0.3, math.sin(a) * 0.3, 0.15), 'scrap')


def colonial_locker():
    """White ceramic, gold trim, a keypad and a blue status light (STARPORT_REACH.md, Chests)."""
    cube((1.5, 0.8, 0.66), (0, 0, 0.33), 'crate')
    cube((1.56, 0.86, 0.14), (0, 0, 0.73), 'ceramic')                 # the lid
    cube((1.58, 0.88, 0.05), (0, 0, 0.665), 'trim')                   # the gold seam under the lid
    for x in (-0.76, 0.76):                                           # gold corner posts
        for y in (-0.41, 0.41):
            cube((0.07, 0.07, 0.7), (x, y, 0.35), 'trim')
    cube((1.4, 0.06, 0.08), (0, -0.42, 0.06), 'trim')                 # kick plates
    cube((1.4, 0.06, 0.08), (0, 0.42, 0.06), 'trim')
    fit_front(cube((0.34, 0.03, 0.26), (0.38, -0.415, 0.4), 'keypad'))
    cube((0.24, 0.025, 0.035), (-0.3, -0.413, 0.56), 'seam')         # the status light


def ashrunner_crate():
    cube((1.1, 0.6, 0.5), (0, 0, 0.25), 'scrap')
    for x in (-0.35, 0.35):
        cube((0.08, 0.64, 0.54), (x, 0, 0.27), 'salvage')
    cube((0.7, 0.62, 0.02), (0, 0, 0.51), 'tarp', rotation=(0, 0.04, 0.05))


def glass_shards(key='glass'):
    rng = random.Random(3)
    for i in range(7):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0, 0.45)
        shard(rng.uniform(0.4, 1.3), rng.uniform(0.08, 0.18), (math.cos(a) * r, math.sin(a) * r, 0), key, i,
              lean=rng.uniform(-0.25, 0.25))


def glass_boulder(key='glass'):
    faceted_rock(0.8, (0, 0, 0.55), key, 9, stretch=(1.2, 1.0, 0.8))
    faceted_rock(0.35, (0.75, 0.3, 0.2), key, 10)


def drone_wreck():
    """A seeker drone shot down (the concept sheet's wreck): a white-and-gold sphere with a dark lens, sunk on one
    side, its shell broken open, shell plates fallen round it."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=8, radius=0.5, location=(0, 0, 0.4))
    sphere = bpy.context.active_object
    bm = bmesh.new()
    bm.from_mesh(sphere.data)
    for face in [f for f in bm.faces if f.calc_center_median().x > 0.2 and f.calc_center_median().z > -0.1]:
        bm.faces.remove(face)                       # the shell is broken open on one side
    bm.to_mesh(sphere.data)
    sphere.data.update()
    sphere.rotation_euler = (0.3, 0.25, 0)
    finish(sphere, 'ceramic')
    sphere.modifiers.new('shell', 'SOLIDIFY').thickness = 0.04
    bpy.context.view_layer.objects.active = sphere
    bpy.ops.object.modifier_apply(modifier='shell')
    cylinder(0.505, 0.06, (0, 0, 0.4), 'trim', 14, rotation=(0.3, 0.25, 0))
    cylinder(0.2, 0.1, (-0.08, -0.47, 0.5), 'trim', 14, rotation=(math.pi / 2 + 0.3, 0, 0))
    cylinder(0.15, 0.04, (-0.08, -0.53, 0.52), 'glass', 14, rotation=(math.pi / 2 + 0.3, 0, 0))
    cube((0.3, 0.3, 0.3), (0.05, 0.05, 0.4), 'console', rotation=(0.2, 0.1, 0.5))
    for i, (x, y, rz) in enumerate([(0.75, 0.15, 0.4), (0.6, -0.45, 1.3), (0.95, -0.15, 2.2), (-0.55, 0.5, 0.8)]):
        cube((0.32, 0.24, 0.035), (x, y, 0.06 + 0.04 * i), 'ceramic', rotation=(0.15 * (i - 1), 0.35, rz))
    cube((0.5, 0.06, 0.05), (0.2, 0.62, 0.05), 'trim', rotation=(0, 0, 0.6))


def relay_post():
    """Aster's relay post: a white-gold pillar with a crystal in a gold cradle. Its glow is its light group."""
    cube((0.7, 0.7, 0.18), (0, 0, 0.09), 'panel')
    cube((0.56, 0.56, 0.1), (0, 0, 0.23), 'trim')
    cylinder(0.15, 1.5, (0, 0, 1.03), 'ceramic', 8)
    for z in (0.45, 1.6, 1.78):
        cylinder(0.19, 0.06, (0, 0, z), 'trim', 8)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        cube((0.05, 0.05, 0.45), (math.cos(a) * 0.17, math.sin(a) * 0.17, 1.98), 'trim',
             rotation=(-math.sin(a) * 0.3, math.cos(a) * 0.3, 0))
    bipyramid(0.13, 0.6, (0, 0, 2.05), 'glass_blue')


def baggage_cart(tipped=False):
    def cart():
        cube((1.5, 0.75, 0.06), (0, 0, 0.3), 'plate')
        for y in (-0.36, 0.36):
            cube((1.5, 0.04, 0.22), (0, y, 0.44), 'trim')
            cube((0.05, 0.05, 0.7), (-0.75, y * 1.03, 0.65), 'girder')    # not flush with the rail
            for x in (-0.6, 0.6):
                cylinder(0.11, 0.07, (x, y, 0.11), 'girder', 12, rotation=(math.pi / 2, 0, 0))
        cube((0.04, 0.76, 0.04), (-0.75, 0, 1.0), 'girder')
        cube((0.6, 0.42, 0.25), (0.25, 0, 0.46), 'crate', rotation=(0, 0, 0.1))
    body = assemble(cart, (0, 0, 0), (1.5, 0, 0.35) if tipped else (0, 0, 0))
    if tipped:
        cube((0.6, 0.42, 0.25), (0.7, -0.75, 0.125), 'crate', rotation=(0, 0, 0.7))
    return body


def shelf_rack(load):
    rng = random.Random(7 if load == 'boxes' else 8)
    w, d, h = 1.8, 0.55, 2.1
    for x in (-w / 2 + 0.03, w / 2 - 0.03):
        for y in (-d / 2 + 0.03, d / 2 - 0.03):
            cube((0.06, 0.06, h), (x, y, h / 2), 'girder')
    for z in (0.12, 0.65, 1.2, 1.75):
        cube((w, d, 0.04), (0, 0, z), 'plate')
        x = -w / 2 + 0.12
        while x < w / 2 - 0.35:
            if load == 'boxes' or rng.random() < 0.4:
                sx, sz = rng.uniform(0.25, 0.45), rng.uniform(0.18, 0.4)
                cube((sx, rng.uniform(0.3, 0.45), sz), (x + sx / 2, rng.uniform(-0.04, 0.04), z + 0.02 + sz / 2),
                     'crate', rotation=(0, 0, rng.uniform(-0.12, 0.12)))
                x += sx + rng.uniform(0.04, 0.15)
            elif rng.random() < 0.5:
                cylinder(0.13, 0.32, (x + 0.13, 0, z + 0.18), 'salvage', 10)
                x += 0.32
            else:
                cylinder(0.05, 0.5, (x + 0.25, rng.uniform(-0.1, 0.1), z + 0.07), 'girder', 8,
                         rotation=(0, math.pi / 2, rng.uniform(-0.2, 0.2)))
                x += 0.55


def luggage_pile():
    def case(size):
        def parts():
            cube(size, (0, 0, 0), 'ceramic')
            for x in (-size[0] * 0.28, size[0] * 0.28):
                cube((0.05, size[1] + 0.02, size[2] + 0.02), (x, 0, 0), 'trim')
            cube((0.16, 0.03, 0.04), (0, 0, size[2] / 2 + 0.02), 'girder')
        return parts

    def bag():
        cylinder(0.17, 0.55, (0, 0, 0), 'cloth', 10, rotation=(0, math.pi / 2, 0))
        bpy.context.active_object.scale = (1, 1, 0.7)
        cube((0.1, 0.04, 0.06), (0, 0, 0.13), 'plank')

    assemble(case((0.7, 0.45, 0.22)), (0, 0, 0.11), (0, 0, 0.2))
    assemble(case((0.6, 0.4, 0.2)), (0.05, 0.02, 0.33), (0, 0, -0.3))
    assemble(case((0.65, 0.45, 0.24)), (0.85, 0.3, 0.12), (0, 0, 1.1))
    assemble(case((0.6, 0.45, 0.22)), (-0.62, 0.42, 0.24), (math.pi / 2, 0, 0.4))
    assemble(bag, (0.3, -0.55, 0.12), (0, 0, 0.6))
    assemble(bag, (-0.35, -0.45, 0.12), (0, 0, -0.9))
    assemble(bag, (0.8, 0.28, 0.36), (0.2, 0, 1.3))


def bench():
    cube((1.9, 0.45, 0.08), (0, 0, 0.45), 'ceramic')
    cube((1.92, 0.47, 0.03), (0, 0, 0.4), 'trim')
    for x in (-0.7, 0.7):
        cube((0.12, 0.38, 0.39), (x, 0, 0.195), 'panel')
        cube((0.08, 0.06, 0.36), (x, 0.2, 0.66), 'trim')
    cube((1.9, 0.06, 0.38), (0, 0.22, 0.8), 'ceramic', rotation=(-0.12, 0, 0))


def fallen_plates():
    rng = random.Random(11)
    for size, location, rotation in [((1.25, 0.9, 0.06), (0, 0, 0.03), (0, 0, 0.3)),
                                     ((1.1, 0.8, 0.06), (0.35, 0.25, 0.1), (0.08, -0.05, -0.4)),
                                     ((0.9, 0.7, 0.06), (-0.75, 0.2, 0.32), (0, 0.6, 0.15)),
                                     ((0.7, 0.55, 0.06), (0.9, -0.45, 0.05), (0, 0, 1.2)),
                                     ((0.6, 0.45, 0.05), (-0.3, -0.6, 0.18), (0.4, 0, 2.0))]:
        cube(size, location, 'panel', rotation=rotation)
    for i in range(7):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0.3, 1.2)
        faceted_rock(rng.uniform(0.06, 0.14), (math.cos(a) * r, math.sin(a) * r, 0.05), 'ceramic', 30 + i,
                     stretch=(1.2, 1.0, 0.6))


def hanging_lamp():
    """A salvage lamp on a chain; the bottom is the model's origin and the chain's top its height."""
    cylinder(0.09, 0.03, (0, 0, 2.08), 'scrap', 8)
    cylinder(0.012, 1.0, (0, 0, 1.57), 'girder', 6)
    cone(0.22, 0.05, 0.14, (0, 0, 1.0), 'scrap', 12)
    cylinder(0.1, 0.24, (0, 0, 0.82), 'lamp', 10)
    for i in range(4):
        a = i * math.pi / 2
        cube((0.02, 0.02, 0.26), (math.cos(a) * 0.115, math.sin(a) * 0.115, 0.82), 'girder')
    cylinder(0.13, 0.04, (0, 0, 0.68), 'scrap', 10)


def lamp_string():
    """A cable sagging 0.6 between hooks 6 apart, a small lamp every metre."""
    span, sag, segments = 6.0, 0.6, 12

    def z(x):
        return 1.0 + sag * ((2 * x / span) ** 2 - 1)

    for i in range(segments):
        x0, x1 = -span / 2 + span * i / segments, -span / 2 + span * (i + 1) / segments
        angle = math.atan2(z(x1) - z(x0), x1 - x0)
        length = math.hypot(x1 - x0, z(x1) - z(x0))
        cylinder(0.012, length, ((x0 + x1) / 2, 0, (z(x0) + z(x1)) / 2), 'girder', 6,
                 rotation=(0, math.pi / 2 - angle, 0))
    for x in (-span / 2, span / 2):
        cube((0.06, 0.06, 0.1), (x, 0, z(x) + 0.03), 'girder')
    for k in range(1, 6):
        x = -span / 2 + k
        cylinder(0.03, 0.04, (x, 0, z(x) - 0.04), 'scrap', 8)
        cylinder(0.045, 0.1, (x, 0, z(x) - 0.11), 'lamp', 8)


def drum():
    cylinder(0.3, 0.85, (0, 0, 0.425), 'salvage', 14)
    for zz in (0.2, 0.65):
        cylinder(0.31, 0.04, (0, 0, zz), 'scrap', 14)
    cylinder(0.29, 0.03, (0, 0, 0.865), 'scrap', 14)
    cylinder(0.04, 0.03, (0.15, 0, 0.89), 'girder', 8)


def drum_clean():
    """The Hesperians' own drum: a white ceramic colony canister with gold bands and lid (Lowhold, the village)."""
    cylinder(0.3, 0.85, (0, 0, 0.425), 'ceramic', 16)
    for zz in (0.2, 0.65):
        cylinder(0.31, 0.04, (0, 0, zz), 'trim', 16)
    cylinder(0.31, 0.04, (0, 0, 0.87), 'trim', 16)
    cylinder(0.05, 0.03, (0.15, 0, 0.9), 'trim', 8)


def brazier_clean():
    """A ceramic fire bowl on a gold tripod (the flame is the decoration's effect)."""
    cylinder(0.34, 0.22, (0, 0, 0.62), 'ceramic', 16)
    cylinder(0.3, 0.06, (0, 0, 0.73), 'resin', 16)
    cylinder(0.36, 0.04, (0, 0, 0.74), 'trim', 16)
    for i in range(3):
        a = i * 2 * math.pi / 3
        cube((0.05, 0.05, 0.56), (math.cos(a) * 0.22, math.sin(a) * 0.22, 0.28), 'trim', rotation=(0, 0, a))


def crate_clean():
    """A colony supply crate: white ceramic composite with gold corners."""
    cube((0.9, 0.6, 0.55), (0, 0, 0.275), 'colony_crate')
    for x in (-0.44, 0.44):
        for y in (-0.29, 0.29):
            cube((0.05, 0.05, 0.57), (x, y, 0.285), 'trim')


def open_tube(radius, depth, location, key, vertices=18, bottom=False, thickness=0.0):
    """A cylinder without its top (and without its bottom unless bottom), walls `thickness` thick inward when set."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.active_object
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    caps = [f for f in mesh.faces if abs(f.normal.z) > 0.9 and (f.normal.z > 0 or not bottom)]
    bmesh.ops.delete(mesh, geom=caps, context='FACES')
    mesh.to_mesh(obj.data)
    mesh.free()
    if thickness:
        modifier = obj.modifiers.new('wall', 'SOLIDIFY')
        modifier.thickness = thickness
        modifier.offset = -1.0
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier='wall')
    return finish(obj, key)


def stat_barrel(liquid):
    """A stat barrel as MM6-8's: an open barrel full of a coloured liquid, +2 to one stat, empty once drunk. The
    Hesperians' white ceramic drum (hes_drum_clean), larger and open-topped: walls with thickness, a rolled gold rim,
    gold bands, the liquid surface a hand below the rim and a glowing gauge strip down its front (-y) showing the
    colour from the street. hes_stat_barrel_empty is the same drum drained: its inside and floor showing, a dark
    residue on the floor."""
    open_tube(0.36, 0.95, (0, 0, 0.475), 'ceramic', 20, bottom=True, thickness=0.035)
    for zz in (0.22, 0.72):
        open_tube(0.372, 0.05, (0, 0, zz), 'trim', 20, bottom=False)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.343, minor_radius=0.028, major_segments=24, minor_segments=6,
                                     location=(0, 0, 0.95))
    finish(bpy.context.active_object, 'trim')                                 # the rolled rim
    if liquid == 'empty':
        cylinder(0.3, 0.008, (0, 0, 0.04), 'liquid_empty', 20)                # residue on the floor
    else:
        cylinder(0.322, 0.01, (0, 0, 0.85), 'liquid_' + liquid, 20)           # the liquid, a hand below the rim
    cube((0.07, 0.02, 0.36), (0, -0.362, 0.47), 'liquid_' + liquid)          # the gauge strip
    cube((0.11, 0.015, 0.42), (0, -0.354, 0.47), 'trim')                     # its gold frame


def fountain():
    """Landfall's fountain: an Ancient purifier the settlers found still running. An octagonal white ceramic basin
    with a gold rim, its water, and a fluted column with gold bands rising from it to a gold bowl that spills four
    thin streams back into the basin, an energy crystal glowing over the bowl. About 3.4 m across, 2.6 m tall."""
    cylinder(1.7, 0.55, (0, 0, 0.275), 'ceramic', 8, rotation=(0, 0, math.pi / 8))
    cylinder(1.76, 0.07, (0, 0, 0.56), 'trim', 8, rotation=(0, 0, math.pi / 8))
    cylinder(1.56, 0.02, (0, 0, 0.6), 'water', 8, rotation=(0, 0, math.pi / 8))
    cylinder(1.9, 0.12, (0, 0, 0.06), 'plate', 8, rotation=(0, 0, math.pi / 8))     # the step round it
    cylinder(0.24, 1.6, (0, 0, 1.3), 'ceramic', 12)
    for k in range(8):                                                          # the column's flutes
        a = k * math.pi / 4
        cube((0.03, 0.03, 1.4), (math.cos(a) * 0.245, math.sin(a) * 0.245, 1.3), 'trim', rotation=(0, 0, a))
    for zz in (0.68, 1.95):
        cylinder(0.29, 0.06, (0, 0, zz), 'trim', 12)
    cone(0.18, 0.62, 0.3, (0, 0, 2.2), 'trim', 12)                              # the bowl
    cylinder(0.56, 0.02, (0, 0, 2.34), 'water', 12)
    for k in range(4):                                                          # its four streams
        a = k * math.pi / 2 + math.pi / 4
        cylinder(0.025, 1.72, (math.cos(a) * 0.58, math.sin(a) * 0.58, 1.48), 'water', 6)
    bipyramid(0.1, 0.32, (0, 0, 2.62), 'energy', 6)


def energy_lamp():
    """An Ancient energy lamp hung on a gold rod: a glowing crystal column in a gold cage under a ceramic cap; the
    bottom is the model's origin and the rod's top its height (as hes_hanging_lamp, 1.43)."""
    cylinder(0.07, 0.03, (0, 0, 2.08), 'trim', 10)
    cylinder(0.012, 0.95, (0, 0, 1.6), 'trim', 6)
    cone(0.16, 0.06, 0.12, (0, 0, 1.08), 'ceramic', 12)
    cylinder(0.065, 0.3, (0, 0, 0.86), 'energy', 10)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        cube((0.018, 0.018, 0.34), (math.cos(a) * 0.1, math.sin(a) * 0.1, 0.86), 'trim')
    cylinder(0.12, 0.04, (0, 0, 0.68), 'trim', 12)
    bipyramid(0.05, 0.12, (0, 0, 0.62), 'energy', 6)


def wall_light(diffuser):
    """A colony wall light: a tall frosted diffuser in three cells in a gold frame on a white ceramic back plate, a
    small gold point above. Its back is the plane y = 0 (the wall), its front faces -y."""
    cube((0.42, 0.05, 1.0), (0, -0.025, 0.5), 'ceramic')
    for x in (-0.1925, 0.1925):
        cube((0.035, 0.03, 1.0), (x, -0.065, 0.5), 'trim')
    for z in (0.0175, 0.9825):
        cube((0.35, 0.03, 0.035), (0, -0.065, z), 'trim')
    cube((0.30, 0.02, 0.86), (0, -0.06, 0.5), diffuser)
    for z in (0.36, 0.64):
        cube((0.32, 0.03, 0.03), (0, -0.07, z), 'ceramic')
    cone(0.07, 0.0, 0.09, (0, -0.035, 1.045), 'trim', 4, rotation=(0, 0, math.pi / 4))


def ceiling_light(diffuser):
    """A colony ceiling panel, 1.2 x 0.6 m: a frosted diffuser in two cells under a white ceramic housing, framed in
    gold. Its top (z 0.07) goes against the ceiling, the diffuser faces down."""
    cube((1.2, 0.6, 0.05), (0, 0, 0.045), 'ceramic')
    cube((1.04, 0.44, 0.02), (0, 0, 0.01), diffuser)
    for y in (-0.24, 0.24):
        cube((1.12, 0.04, 0.025), (0, y, 0.0125), 'trim')
    for x in (-0.54, 0.0, 0.54):
        cube((0.04, 0.48, 0.025), (x, 0, 0.0125), 'trim' if x else 'ceramic')


def light_pylon():
    """A standing colony light for the great halls: a white ceramic post on an octagonal plinth, a crystal of cool
    light in a gold cage at the top (2.7 m)."""
    cylinder(0.22, 0.12, (0, 0, 0.06), 'ceramic', 8)
    cylinder(0.24, 0.03, (0, 0, 0.135), 'trim', 8)
    cylinder(0.07, 1.9, (0, 0, 1.1), 'ceramic', 8)
    cylinder(0.12, 0.05, (0, 0, 2.075), 'trim', 8)
    cylinder(0.08, 0.45, (0, 0, 2.325), 'diffuser_white', 6)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        cube((0.022, 0.022, 0.5), (math.cos(a) * 0.11, math.sin(a) * 0.11, 2.325), 'trim')
    cone(0.13, 0.0, 0.16, (0, 0, 2.63), 'trim', 8)


def valve_body(opened):
    """A drain valve's fixed part on the wall: a ceramic pipe rising from the floor into a gold-banded valve body and a
    status lamp beside the wheel's stem, red shut and green open. The wheel (hes_valve_wheel) mounts in front of it.
    Back on the plane y = 0 (the wall), front -y."""
    cylinder(0.09, 1.7, (0, -0.13, 0.85), 'ceramic', 12)
    for z in (0.08, 1.65):
        cylinder(0.11, 0.05, (0, -0.13, z), 'trim', 12)
    cube((0.32, 0.26, 0.3), (0, -0.13, 1.4), 'ceramic')
    cube((0.34, 0.2, 0.04), (0, -0.13, 1.26), 'trim')
    cube((0.34, 0.2, 0.04), (0, -0.13, 1.54), 'trim')
    cube((0.08, 0.04, 0.6), (0, -0.02, 1.4), 'trim')                         # the wall bracket
    cylinder(0.04, 0.04, (0.12, -0.27, 1.5), 'lamp_green' if opened else 'lamp_red', 8,
             rotation=(math.pi / 2, 0, 0))


def valve_wheel(turned):
    """A drain valve's gold handwheel (five spokes, a red pointer on the hub) on its stem from the wall, whose plane
    y = 0 is the model's back, so it mounts in front of the valve body. The turned one is a quarter turn round: its
    binding turns it there when the valve is opened (turn_in)."""
    turn = math.pi / 2 if turned else 0.0
    cylinder(0.035, 0.5, (0, -0.25, 0.33), 'trim', 8, rotation=(math.pi / 2, 0, 0))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.3, minor_radius=0.03, major_segments=20, minor_segments=6,
                                     location=(0, -0.5, 0.33), rotation=(math.pi / 2, 0, 0))
    finish(bpy.context.active_object, 'trim')
    for k in range(5):
        a = turn + k * 2 * math.pi / 5
        cube((0.03, 0.03, 0.3), (math.sin(a) * 0.15, -0.5, 0.33 + math.cos(a) * 0.15), 'trim', rotation=(0, a, 0))
    cylinder(0.07, 0.06, (0, -0.5, 0.33), 'ceramic', 10, rotation=(math.pi / 2, 0, 0))
    cube((0.03, 0.02, 0.13), (math.sin(turn) * 0.08, -0.535, 0.33 + math.cos(turn) * 0.08), 'lamp_red',
         rotation=(0, turn, 0))


# The turret actors' side counts per LOD (0 = the decoration's and the actor's full detail; 1..3 the actor's authored
# LODs, about half the triangles per level); None leaves the part out. A band has its drum's count so its corners
# stay outside the drum's; a cooling ring encloses its barrel at any count here.
TURRET_SIDES = {
    False: {'neck': (16, 10, 6, 6), 'drum': (24, 12, 8, 8), 'band': (24, 12, 8, None), 'barrel': (16, 10, 6, 6),
            'ring': (16, 8, 6, None), 'cell': (16, 10, 6, 6), 'lens': (12, 8, 6, None), 'rod': (8, 6, 4, 4)},
    True: {'neck': (20, 12, 8, 6), 'drum': (24, 14, 10, 8), 'band': (24, 14, 10, None), 'barrel': (16, 8, 6, 6),
           'ring': (16, 6, None, None), 'cell': (16, 8, 6, 6), 'lens': (12, 8, 6, None),
           'shoulder_trim': (True, True, True, None)},
}


def turret(heavy, part='all', lod=0):
    """Landfall's wall turrets (concepts/monsters/ward_turret.png, gate_bastion.png): a kept-up Ancient turret head of
    white ceramic and gold, its emitters and sensor lenses glowing blue-white, on the settlers' prefab mount. The
    Ward Turret has one long barrel and a Hesperian pennant; the Gate Bastion is broader, two barrels, armoured
    shoulders and three lenses. The barrels point along -y (the front); the base's bottom is the model's foot.
    part: 'all' the whole turret (the decoration), 'mount' the pedestal up to and with the gold turning ring (the
    decoration under the turret actor), 'head' the neck, housing, lenses and pennant or shoulders (they turn on the
    ring), 'barrel' the barrels with their rings and emitters (they pitch on the housing). Returns the pivots:
    the ring's top centre, the barrels' pitch axis point and the emitter tips. lod: the head and barrel's level of
    detail (`TURRET_SIDES`; the mount has one level)."""
    s = 1.35 if heavy else 1.0
    sides = {key: counts[lod] for key, counts in TURRET_SIDES[heavy].items()}
    mount, head, barrel = (part in ('all', key) for key in ('mount', 'head', 'barrel'))
    top = 0.7
    if mount and heavy:                                    # an octagonal prefab plinth in two steps
        cylinder(0.95, 0.25, (0, 0, 0.125), 'prefab', 8, rotation=(0, 0, math.pi / 8))
        cylinder(0.78, 0.45, (0, 0, 0.475), 'prefab', 8, rotation=(0, 0, math.pi / 8))
        cube((0.5, 0.03, 0.32), (0, -0.735, 0.47), 'banner')                    # the Hesperian plate on the front
    elif mount:                                            # a square deck plate, a round pedestal
        cube((1.3, 1.3, 0.08), (0, 0, 0.04), 'prefab')
        for x in (-0.55, 0.55):
            for y in (-0.55, 0.55):
                cylinder(0.06, 0.07, (x, y, 0.1), 'trim', 6)
        round_cylinder(0.52, 0.62, (0, 0, 0.39), 'prefab', 24)
        cube((0.26, 0.03, 0.3), (0, -0.515, 0.36), 'hazard')                      # the access hatch, its back
    if mount:                                                                     # edges just in the round
        round_cylinder(0.56 * s, 0.07, (0, 0, top + 0.035), 'trim', 32)           # the turning ring
    hz = top + 0.31 + 0.4 * s                                                     # the head's axis height
    if head:
        round_cylinder(0.26 * s, 0.25, (0, 0, top + 0.19), 'trim', sides['neck'])           # the neck
        # The head: a ceramic drum lying front to back with tapered ends (one closed surface: the drum, its two
        # cones to the flat end faces; hard edges where the cones meet the drum and the faces) and gold bands.
        lathe([(0.18 * s, -0.62 * s), (0.42 * s, -0.4 * s), (0.42 * s, 0.4 * s), (0.18 * s, 0.62 * s)], (0, 0, hz),
              'ceramic', sides['drum'], rotation=(math.pi / 2, 0, 0))
        for y in (-0.25 * s, 0.25 * s) if sides['band'] else ():
            round_cylinder(0.44 * s, 0.05, (0, y, hz), 'trim', sides['band'], rotation=(math.pi / 2, 0, 0))
    barrels = (-0.17 * s, 0.17 * s) if heavy else (0.0,)
    bz = hz + (0.05 if heavy else 0.0)
    length = 1.5 * s
    tips = [(bx, -0.5 * s - length - 0.14, bz) for bx in barrels]
    for bx in barrels if barrel else ():
        round_cylinder(0.08 * s, length, (bx, -0.5 * s - length / 2, bz), 'ceramic', sides['barrel'],
                       rotation=(math.pi / 2, 0, 0))
        for k in range(3 if not heavy else 5) if sides['ring'] else ():          # cooling rings or fins
            round_cylinder(0.11 * s, 0.05, (bx, -0.65 * s - k * 0.2 * s, bz), 'trim', sides['ring'],
                           rotation=(math.pi / 2, 0, 0))
        round_cylinder(0.105 * s, 0.14, (bx, -0.5 * s - length - 0.07, bz), 'cell', sides['cell'],
                       rotation=(math.pi / 2, 0, 0))
    if head:
        lenses = (-0.12, 0.0, 0.12) if heavy else (0.24,)
        for lx in lenses if sides['lens'] else ():
            round_cylinder(0.07 * s, 0.05, (lx * s if heavy else lx, -0.52 * s, hz - (0.2 * s if heavy else -0.12)),
                           'cell', sides['lens'], rotation=(math.pi / 2, 0, 0))
    if head and heavy:                                     # the armoured shoulders, a settler patch plate
        for x in (-0.5 * s, 0.5 * s):
            cube((0.14 * s, 0.7 * s, 0.6 * s), (x, 0.05 * s, hz + 0.05), 'ceramic')
            if sides['shoulder_trim']:
                cube((0.16 * s, 0.4 * s, 0.08 * s), (x, 0.05 * s, hz + 0.37 * s), 'trim')
        cube((0.03, 0.4 * s, 0.35 * s), (0.43 * s, 0.25 * s, hz - 0.05), 'prefab')
    elif head:                                             # the pennant on its rod at the back
        round_cylinder(0.015, 0.5, (-0.3, 0.35, hz + 0.32), 'trim', sides['rod'], rotation=(0, math.pi / 2, 0))
        cube((0.02, 0.3, 0.55), (-0.5, 0.35, hz + 0.05), 'banner')
    return {'ring': (0.0, 0.0, top + 0.07), 'pitch': (0.0, 0.0, bz), 'tips': tips}


def goods_cells():
    """Market goods of the Hesperians: an open colony crate of glowing Shield Cells beside a tray of algae ration bricks
    and a small gold-banded case."""
    w, d, h = 0.7, 0.5, 0.34
    cube((w, d, 0.04), (0, 0, 0.02), 'colony_crate')
    for x in (-w / 2, w / 2):
        cube((0.03, d, h), (x, 0, h / 2), 'colony_crate')
    for y in (-d / 2, d / 2):
        cube((w, 0.03, h), (0, y, h / 2), 'colony_crate')
    for x in (-w / 2, w / 2):
        for y in (-d / 2, d / 2):
            cube((0.04, 0.04, h + 0.02), (x, y, h / 2 + 0.01), 'trim')
    for i in range(4):
        for j in range(3):
            x, y = -0.24 + i * 0.16, -0.14 + j * 0.14
            cylinder(0.045, 0.22, (x, y, 0.15), 'cell', 10)
            cylinder(0.05, 0.03, (x, y, 0.27), 'trim', 10)
    cube((0.5, 0.36, 0.03), (0.68, 0.05, 0.015), 'ceramic')
    for i in range(3):
        for j in range(2):
            cube((0.14, 0.1, 0.06), (0.52 + i * 0.16, -0.06 + j * 0.2, 0.06), 'resin')
    cube((0.34, 0.24, 0.18), (-0.62, 0.12, 0.09), 'ceramic', rotation=(0, 0, 0.4))
    cube((0.35, 0.025, 0.04), (-0.62, 0.12, 0.13), 'trim', rotation=(0, 0, 0.4))


def offerings_crystal():
    """Offerings to Aster: a wide ceramic bowl of glowing data crystals on a gold ring stand."""
    cylinder(0.22, 0.06, (0, 0, 0.03), 'trim', 16)
    cylinder(0.08, 0.14, (0, 0, 0.12), 'trim', 12)
    cone(0.18, 0.36, 0.16, (0, 0, 0.27), 'ceramic', 16)
    rng = random.Random(9)
    for k in range(6):
        a, r = k * math.pi / 3 + rng.uniform(-0.2, 0.2), rng.uniform(0.08, 0.2)
        bipyramid(rng.uniform(0.03, 0.05), rng.uniform(0.18, 0.3), (math.cos(a) * r, math.sin(a) * r, 0.38),
                  'energy', 6, rotation=(rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 0))
    bipyramid(0.06, 0.42, (0, 0, 0.42), 'energy', 6)


def bedroll():
    cube((0.8, 1.9, 0.04), (0, 0, 0.02), 'rug', rotation=(0, 0, 0.04))
    cylinder(0.14, 0.8, (0, -0.85, 0.14), 'cloth', 12, rotation=(0, math.pi / 2, 0))
    for x in (-0.25, 0.25):
        cylinder(0.145, 0.03, (x, -0.85, 0.14), 'plank', 12, rotation=(0, math.pi / 2, 0))
    cube((0.45, 0.28, 0.1), (0, 0.72, 0.09), 'cloth', rotation=(0, 0, 0.08))


def offerings():
    rng = random.Random(5)
    for i in range(7):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0.05, 0.35)
        hgt, rad = rng.uniform(0.1, 0.3), rng.uniform(0.025, 0.045)
        x, y = math.cos(a) * r, math.sin(a) * r * 0.7 - 0.05
        cylinder(rad, hgt, (x, y, hgt / 2), 'wax', 8)
        bipyramid(rad * 0.6, 0.07, (x, y, hgt + 0.03), 'flame', 4)
    for x, y in ((-0.38, -0.2), (0.4, 0.05)):
        cylinder(0.1, 0.05, (x, y, 0.025), 'trim', 12)
    cube((0.3, 0.24, 0.04), (0.15, -0.3, 0.02), 'rug', rotation=(0, 0, 0.3))
    bipyramid(0.04, 0.18, (-0.38, -0.2, 0.08), 'glass_blue', 6, rotation=(math.pi / 2, 0, 0.5))
    cube((0.06, 0.06, 0.7), (0, 0.32, 0.35), 'plank')
    for k, x in enumerate((-0.05, 0.0, 0.05)):
        cube((0.035, 0.008, 0.35), (x, 0.36, 0.48 - 0.04 * k), 'cloth', rotation=(0.1, 0, 0))


def casket():
    cube((1.5, 0.8, 0.08), (0, 0, 0.04), 'trim')
    cube((1.4, 0.7, 0.5), (0, 0, 0.33), 'marble')
    cube((1.405, 0.705, 0.025), (0, 0, 0.59), 'seam')
    cube((1.42, 0.72, 0.12), (0, 0, 0.66), 'marble')
    cube((1.2, 0.5, 0.06), (0, 0, 0.75), 'trim')
    for x in (-0.69, 0.69):
        for y in (-0.34, 0.34):
            cube((0.05, 0.05, 0.62), (x, y, 0.39), 'trim')
    cube((0.4, 0.02, 0.18), (0, -0.355, 0.32), 'trim')


def lectern():
    cylinder(0.3, 0.06, (0, 0, 0.03), 'trim', 8)
    cylinder(0.1, 0.95, (0, 0, 0.53), 'ceramic', 8)
    tilt = 0.35
    normal = Vector((0, -math.sin(tilt), math.cos(tilt)))
    centre = Vector((0, 0, 1.05))
    cube((0.6, 0.45, 0.05), centre, 'ceramic', rotation=(tilt, 0, 0))
    cube((0.46, 0.32, 0.02), centre + normal * 0.034, 'glass', rotation=(tilt, 0, 0))
    cube((0.62, 0.04, 0.06), centre + Vector((0, -0.23 * math.cos(tilt), -0.23 * math.sin(tilt))), 'trim',
         rotation=(tilt, 0, 0))


def crystal_socket():
    """A socket for an Aster shard; it glows by its own light when the shard is restored."""
    cylinder(0.12, 0.04, (0, 0, 0.02), 'trim', 8)
    cylinder(0.05, 0.25, (0, 0, 0.165), 'trim', 8)
    cone(0.06, 0.14, 0.12, (0, 0, 0.35), 'trim', 8)
    bipyramid(0.07, 0.28, (0, 0, 0.44), 'glass_blue')


MODELS = {'hes_pylon': pylon, 'hes_container': container, 'hes_fuel_tank': fuel_tank,
          'hes_gantry_segment': gantry_segment, 'hes_signpost': signpost, 'hes_tablet_plinth': tablet_plinth,
          'hes_brazier': brazier, 'hes_colonial_locker': colonial_locker, 'hes_ashrunner_crate': ashrunner_crate,
          'hes_glass_shards': glass_shards, 'hes_glass_boulder': glass_boulder, 'hes_drone_wreck': drone_wreck,
          # The zone 1 interiors (design/kreegan_world/zone1/dungeons/INTERIOR_ART.md).
          'hes_glass_shards_blue': lambda: glass_shards('glass_blue'),
          'hes_glass_boulder_blue': lambda: glass_boulder('glass_blue'),
          'hes_relay_post': relay_post, 'hes_baggage_cart': baggage_cart,
          'hes_baggage_cart_over': lambda: baggage_cart(tipped=True),
          'hes_shelf_rack': lambda: shelf_rack('boxes'), 'hes_shelf_rack_tools': lambda: shelf_rack('tools'),
          'hes_luggage_pile': luggage_pile, 'hes_bench': bench, 'hes_fallen_plates': fallen_plates,
          'hes_hanging_lamp': hanging_lamp, 'hes_lamp_string': lamp_string, 'hes_drum': drum, 'hes_bedroll': bedroll,
          'hes_offerings': offerings, 'hes_casket': casket, 'hes_lectern': lectern,
          'hes_crystal_socket': crystal_socket,
          # The Hesperians' clean colony props (Lowhold, the village), beside the Ashrunners' salvage ones.
          'hes_drum_clean': drum_clean, 'hes_brazier_clean': brazier_clean, 'hes_crate_clean': crate_clean,
          'hes_energy_lamp': energy_lamp, 'hes_goods_cells': goods_cells, 'hes_offerings_crystal': offerings_crystal,
          # The colony light fixtures (the dungeons' and Lowhold's light sources).
          'hes_wall_light': lambda: wall_light('diffuser_white'),
          'hes_wall_light_amber': lambda: wall_light('diffuser_amber'),
          'hes_wall_light_off': lambda: wall_light('diffuser_off'),
          'hes_ceiling_light': lambda: ceiling_light('diffuser_white'),
          'hes_ceiling_light_off': lambda: ceiling_light('diffuser_off'),
          'hes_light_pylon': light_pylon,
          'hes_valve_body': lambda: valve_body(False), 'hes_valve_body_open': lambda: valve_body(True),
          'hes_valve_wheel': lambda: valve_wheel(False), 'hes_valve_wheel_turned': lambda: valve_wheel(True),
          # Landfall's wall turrets (static until the Hesper monster tables are staged).
          'hes_ward_turret': lambda: turret(False), 'hes_gate_bastion': lambda: turret(True),
          # Their mounts under the turret actors are no longer built here (2026-10-22): the v2 turrets are Meshy models
          # and level_generation/creatures/hes_turrets_claude/scripts/build_actor_v2.py writes hes_ward_turret_mount.glb
          # and hes_gate_bastion_mount.glb into work/hard_surface/ (turret(heavy, 'mount') still builds the v1 one;
          # the v1 mounts are kept in hes_turrets_claude/v1_hand_built/mounts/).
          # Landfall's square: the fountain and the stat barrels (MM7's seven colours and the empty barrel).
          'hes_fountain': fountain, 'hes_stat_barrel_empty': lambda: stat_barrel('empty'),
          **{f'hes_stat_barrel_{colour}': (lambda c: lambda: stat_barrel(c))(colour)
             for colour in ('red', 'orange', 'blue', 'yellow', 'green', 'purple', 'white')}}


def build(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MODELS[name]()
    objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects) > 1:
        bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    lowest = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
    obj.location.z -= lowest
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_yup=True,
                              export_apply=True, export_image_format='AUTO')
    dims = obj.dimensions
    print(f'BUILT {name}: {len(obj.data.polygons)} faces, {dims.x:.2f} x {dims.y:.2f} x {dims.z:.2f} m -> {path}')


if __name__ == '__main__':                                 # imported by the turret actor build for its parts
    names = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(MODELS)
    for model in names:
        build(model)
