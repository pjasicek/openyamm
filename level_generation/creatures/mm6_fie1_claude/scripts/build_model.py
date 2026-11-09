"""MM6 fire elemental (fie1): the MPFB core figure with its retargeted clips (work/anim.blend) inside alpha-blended
flame-cage shells revolved from the restored silhouette, hand bursts and death effects on quads, three LOD meshes
and the Standing/Walking/Attack/Hit/Death/Dead clips. Run under Blender:

    blender --background work/anim.blend --python scripts/build_model.py

Units: 1 Blender unit = 100 native logical pixels, origin at the sprite's ground pivot (actors.yml scale 69.9997 =
100 x the native frame scale), forward -Y. Writes textures/fie1_body.png (baked), work/fie1.blend and
export/mm6_fie1_raw.glb (finish_glb.py wires the LODs, sets the runtime materials and the tiers).

Materials, in primitive order: FireElemental_Body (opaque figure, unlit, its shading baked into the texture),
FireElemental_Flame (the cage, alpha blended, single-sided, scrolls upward by texture scroll so the flames rise
continuously across clips), FireElemental_Fringe (radial fins carrying the sprite's outer flame tongues, scrolling
the same way; a fin faces the camera exactly where it forms the silhouette, and is edge-on in front of the body) and
FireElemental_Fx (hand bursts and death effects, alpha blended). The engine draws
opaque primitives first and blended ones in authored order, keeping each blended primitive's triangle order: cage
faces go back to front for any side view (outer shell's inside, inner shell's inside, inner shell's outside, outer
shell's outside); backface culling keeps only the far half of each inside and the near half of each outside.

Rig: the MPFB Mixamo skeleton under a new Root (moves, leans, uniform scale), a vertical Cage chain (sway only) with
a leaf CageW bone per link carrying the cage's width (non-uniform scale on leaves only, so the chain never shears),
BurstL/BurstR leaves on the hands and FxStar/FxSparks/FxEmbers on Root. A hidden part is scaled to 0.001.
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTURES = os.path.join(HERE, 'textures')
PROFILE = json.load(open(os.path.join(TEXTURES, 'fie1_profile.json')))
BODY_COLORS = json.load(open(os.path.join(TEXTURES, 'fie1_body_colors.json')))
FPS = 24
HIDDEN = 0.001
CAGE_BONES = 6
# The walk lean (restored side views: the cage's axis tilts about 20 degrees forward), about mid-cage.
LEAN = math.radians(20.0)
LEAN_PIVOT = 1.25
# Death effects centre: the star of death frame d, 2x pixel row 248 of 512 -> 1.32 above the pivot.
FX_CENTRE = Vector((0.0, 0.0, 1.32))
FX_SIZE = 2.5           # the fx crops are 500 x 2 pixels wide
BURST_SIZE = 0.62       # the hand burst crop is 124 x 2 pixels wide
LODS = [
    {'name': 'FireElemental', 'body': 1.0, 'segments': 28, 'rings': 20, 'shells': 1, 'fins': 12, 'burst_quads': 3},
    {'name': 'FireElemental_LOD1', 'body': 0.5, 'segments': 18, 'rings': 13, 'shells': 1, 'fins': 8,
     'burst_quads': 3},
    {'name': 'FireElemental_LOD2', 'body': 0.25, 'segments': 12, 'rings': 8, 'shells': 1, 'fins': 6,
     'burst_quads': 2},
]
# Cage shells: radius scale, u repeats round (negative mirrors, so the shells' lattices turn opposite ways under
# the shared scroll), u phase, v scale (tiles per cage tile) and v phase.
SHELLS = [
    {'name': 'outer', 'radius': 1.12, 'repeats': 1.0, 'phase': 0.0, 'v_scale': 1.0, 'v_phase': 0.0},
    {'name': 'inner', 'radius': 0.74, 'repeats': -1.0, 'phase': 0.37, 'v_scale': 1.2, 'v_phase': 0.5},
]
# fx atlas quadrants (u0, v0) in glTF orientation (v down the image).
QUAD_BURST, QUAD_STAR, QUAD_SPARKS, QUAD_EMBERS = (0.0, 0.0), (0.5, 0.0), (0.0, 0.5), (0.5, 0.5)

rows = list(zip(PROFILE['height_px'], PROFILE['radius_px'], PROFILE['offset_px']))
CAGE_TOP = rows[0][0] / 100.0
CAGE_TIP = rows[-1][0] / 100.0
TILE_HEIGHT = PROFILE['tile_share'] * (CAGE_TOP - CAGE_TIP)


def profile_at(t):
    """Height, radius and sideways axis offset at t (0 = top, 1 = bottom tip), in Blender units."""
    position = t * (len(rows) - 1)
    index = min(int(position), len(rows) - 2)
    f = position - index
    a, b = rows[index], rows[index + 1]
    return [(a[k] * (1 - f) + b[k] * f) / 100.0 for k in range(3)]


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def action_curves(action):
    return [curve for layer in action.layers for strip in layer.strips for bag in strip.channelbags
            for curve in bag.fcurves]


def assign(rig, action):
    rig.animation_data_create()
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]


# ---------------------------------------------------------------------------------------------------------- rig
def extend_rig(rig):
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    bones = rig.data.edit_bones
    root = bones.new('Root')
    root.head, root.tail = (0, 0, 0), (0, 0, 0.3)
    bones['Hips'].parent = root
    heights = [CAGE_TIP + (CAGE_TOP - CAGE_TIP) * i / CAGE_BONES for i in range(CAGE_BONES + 1)]
    parent = root
    chain = []
    for index in range(CAGE_BONES):
        bone = bones.new(f'Cage{index + 1}')
        bone.head, bone.tail = (0, 0, heights[index]), (0, 0, heights[index + 1])
        bone.parent = parent
        bone.use_connect = index > 0
        parent = bone
        chain.append(bone)
    for index in range(CAGE_BONES):
        bone = bones.new(f'CageW{index + 1}')
        bone.head, bone.tail = chain[index].head.copy(), chain[index].tail.copy()
        bone.parent = chain[index]
    for side, hand in (('L', 'LeftHand'), ('R', 'RightHand')):
        source = bones[hand]
        bone = bones.new(f'Burst{side}')
        # Centred in the palm: half way along the hand bone, which ends at the finger roots.
        centre = (source.head + source.tail) / 2 + (source.tail - source.head) * 0.4
        bone.head, bone.tail = centre, centre + (source.tail - source.head).normalized() * 0.1
        bone.parent = source
    for name in ('FxStar', 'FxSparks', 'FxEmbers'):
        bone = bones.new(name)
        bone.head, bone.tail = FX_CENTRE, FX_CENTRE + Vector((0, 0, 0.3))
        bone.parent = root
    bpy.ops.object.mode_set(mode='OBJECT')
    return heights


# --------------------------------------------------------------------------------------------------- figure
def bake_body_texture(body):
    """Mottled dark red from the restored core colours (noise in object space), shaded by a soft key from the front
    and above plus ambient occlusion, baked into the figure's UVs (the material is unlit in game)."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 64
    scene.cycles.device = 'CPU'
    material = bpy.data.materials.new('FireElemental_Body')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')
    coords = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 7.0
    noise.inputs['Detail'].default_value = 5.0
    noise.inputs['Roughness'].default_value = 0.6
    ramp = nodes.new('ShaderNodeValToRGB')
    stops = [0.3, 0.45, 0.55, 0.68, 0.8]
    elements = ramp.color_ramp.elements
    while len(elements) < len(stops):
        elements.new(0.5)
    for element, position, color in zip(elements, stops, BODY_COLORS['colors']):
        element.position = position
        element.color = tuple(srgb_to_linear(c) for c in color) + (1.0,)
    geometry = nodes.new('ShaderNodeNewGeometry')
    key = nodes.new('ShaderNodeVectorMath')
    key.operation = 'DOT_PRODUCT'
    key.inputs[1].default_value = Vector((0.25, -0.55, 0.8)).normalized()
    shade = nodes.new('ShaderNodeMapRange')
    shade.inputs['From Min'].default_value = -1.0
    shade.inputs['From Max'].default_value = 1.0
    # Darker than the restored core's median: seen in game without the sprite's overlapping flames, a brighter figure
    # outshone the cage.
    shade.inputs['To Min'].default_value = 0.4
    shade.inputs['To Max'].default_value = 0.95
    ao = nodes.new('ShaderNodeAmbientOcclusion')
    ao.inputs['Distance'].default_value = 0.15
    ao_range = nodes.new('ShaderNodeMapRange')
    ao_range.inputs['To Min'].default_value = 0.55
    multiply = nodes.new('ShaderNodeMix')
    multiply.data_type = 'RGBA'
    multiply.blend_type = 'MULTIPLY'
    multiply.inputs['Factor'].default_value = 1.0
    multiply2 = nodes.new('ShaderNodeMix')
    multiply2.data_type = 'RGBA'
    multiply2.blend_type = 'MULTIPLY'
    multiply2.inputs['Factor'].default_value = 1.0
    links.new(coords.outputs['Object'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(geometry.outputs['Normal'], key.inputs[0])
    links.new(key.outputs['Value'], shade.inputs['Value'])
    links.new(ao.outputs['AO'], ao_range.inputs['Value'])
    links.new(ramp.outputs['Color'], multiply.inputs['A'])
    links.new(shade.outputs['Result'], multiply.inputs['B'])
    links.new(multiply.outputs['Result'], multiply2.inputs['A'])
    links.new(ao_range.outputs['Result'], multiply2.inputs['B'])
    links.new(multiply2.outputs['Result'], emission.inputs['Color'])
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    image = bpy.data.images.new('fie1_body', 512, 512)
    target = nodes.new('ShaderNodeTexImage')
    target.image = image
    nodes.active = target
    body.data.materials.clear()
    body.data.materials.append(material)
    for obj in bpy.context.scene.objects:
        obj.select_set(obj == body)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.bake(type='EMIT', margin=8)
    path = os.path.join(TEXTURES, 'fie1_body.png')
    image.filepath_raw = path
    image.file_format = 'PNG'
    image.save()
    # Runtime material: the baked texture as base colour.
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(path, check_existing=False)
    links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return material


def lod_body(body, ratio, name):
    copy = body.copy()
    copy.data = body.data.copy()
    copy.name = copy.data.name = name
    bpy.context.collection.objects.link(copy)
    if ratio < 1.0:
        modifier = copy.modifiers.new('Decimate', 'DECIMATE')
        modifier.ratio = ratio
        modifier.use_symmetry = True
        modifier.symmetry_axis = 'X'
        bpy.context.view_layer.objects.active = copy
        bpy.ops.object.modifier_move_to_index(modifier='Decimate', index=0)
        bpy.ops.object.modifier_apply(modifier='Decimate')
    return copy


# ----------------------------------------------------------------------------------------------------- cage
def shell_rows(shell, rings):
    """(height, radius, offset, v) per ring, top to tip."""
    out = []
    for ring in range(rings):
        t = ring / (rings - 1)
        height, radius, offset = profile_at(t)
        v = shell['v_phase'] + shell['v_scale'] * (CAGE_TOP - height) / TILE_HEIGHT
        out.append((height, max(radius * shell['radius'], 0.01), offset, v))
    return out


def build_fins(lod, heights):
    """Radial fins from FRINGE_INNER to FRINGE_OUTER x the cage radius at every ring, both faces, each on one fringe
    strip with its own v phase."""
    fringe = PROFILE['fringe']
    mesh = bpy.data.meshes.new(lod['name'] + '_fringe')
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    groups = []
    inset = 1.5 / 1024.0
    for fin in range(lod['fins']):
        angle = 2 * math.pi * (fin + 0.5) / lod['fins']
        direction = Vector((math.cos(angle), math.sin(angle), 0.0))
        strip = fin % fringe['strips']
        u0 = strip / fringe['strips'] + inset
        u1 = (strip + 1) / fringe['strips'] - inset
        shell = dict(SHELLS[0], v_phase=0.37 * fin)
        rows_in = shell_rows(shell, lod['rings'])
        for side in (1, -1):
            inner, outer = [], []
            for height, radius, offset, _v in rows_in:
                base = Vector((offset, 0.0, height))
                inner.append(bm.verts.new(base + direction * radius * fringe['inner']))
                outer.append(bm.verts.new(base + direction * radius * fringe['outer']))
                groups.extend([cage_weights(height, heights)] * 2)
            for r in range(len(rows_in) - 1):
                v0, v1 = rows_in[r][3], rows_in[r + 1][3]
                quad = [inner[r], inner[r + 1], outer[r + 1], outer[r]]
                uvs = [(u0, v0), (u0, v1), (u1, v1), (u1, v0)]
                if side == -1:
                    quad, uvs = quad[::-1], uvs[::-1]
                face = bm.faces.new(quad)
                face.smooth = True
                for loop, (u, v) in zip(face.loops, uvs):
                    loop[uv].uv = (u, 1.0 - v)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(lod['name'] + '_fringe', mesh)
    bpy.context.collection.objects.link(obj)
    apply_groups(obj, groups)
    return obj


def build_parts(lod, rig, heights):
    """Cage, burst and fx geometry of one LOD as two objects (flame, fx), weighted to the rig."""
    flame_mesh = bpy.data.meshes.new(lod['name'] + '_flame')
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    groups = []          # per vertex: [(bone, weight)]

    def strip(rows_in, segments, shell, inward):
        grid = []
        for height, radius, offset, _v in rows_in:
            ring = []
            for k in range(segments):
                angle = 2 * math.pi * k / segments
                ring.append(bm.verts.new((offset + radius * math.cos(angle), radius * math.sin(angle), height)))
                groups.append(cage_weights(height, heights))
            grid.append(ring)
        for r in range(len(rows_in) - 1):
            v0, v1 = rows_in[r][3], rows_in[r + 1][3]
            for k in range(segments):
                nxt = (k + 1) % segments
                quad = [grid[r][k], grid[r + 1][k], grid[r + 1][nxt], grid[r][nxt]]
                u0 = shell['phase'] + shell['repeats'] * k / segments
                u1 = shell['phase'] + shell['repeats'] * (k + 1) / segments
                uvs = [(u0, v0), (u0, v1), (u1, v1), (u1, v0)]
                if inward:
                    quad, uvs = quad[::-1], uvs[::-1]
                face = bm.faces.new(quad)
                face.smooth = True
                for loop, (u, v) in zip(face.loops, uvs):
                    loop[uv].uv = (u, 1.0 - v)

    shells = SHELLS[:lod['shells']]
    layers = [(shell_rows(shell, lod['rings']), lod['segments'], shell) for shell in shells]
    for layer in layers:
        strip(*layer, inward=True)
    for layer in reversed(layers):
        strip(*layer, inward=False)
    bm.to_mesh(flame_mesh)
    bm.free()
    flame = bpy.data.objects.new(lod['name'] + '_flame', flame_mesh)
    bpy.context.collection.objects.link(flame)
    apply_groups(flame, groups)

    fx_mesh = bpy.data.meshes.new(lod['name'] + '_fx')
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    groups = []

    def quad(centre, axis_u, axis_v, size, quadrant, bone):
        half_u, half_v = axis_u * (size / 2), axis_v * (size / 2)
        corners = [centre - half_u + half_v, centre - half_u - half_v, centre + half_u - half_v,
                   centre + half_u + half_v]
        uvs = [(0, 0), (0, 1), (1, 1), (1, 0)]
        inset = 2.0 / 1024.0
        for side in (1, -1):    # both faces: the material is single-sided
            verts = [bm.verts.new(c) for c in corners]
            groups.extend([[(bone, 1.0)]] * 4)
            order = range(4) if side == 1 else reversed(range(4))
            order = list(order)
            face = bm.faces.new([verts[i] for i in order])
            for loop, i in zip(face.loops, order):
                u = quadrant[0] + inset + uvs[i][0] * (0.5 - 2 * inset)
                v = quadrant[1] + inset + uvs[i][1] * (0.5 - 2 * inset)
                loop[uv].uv = (u, 1.0 - v)

    x, y, z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
    for side in ('L', 'R'):
        centre = rig.data.bones[f'Burst{side}'].head_local.copy()
        planes = [(x, z), (y, z), (x, y)][:lod['burst_quads']]
        for axis_u, axis_v in planes:
            quad(centre, axis_u, axis_v, BURST_SIZE, QUAD_BURST, f'Burst{side}')
    for quadrant, bone in ((QUAD_STAR, 'FxStar'), (QUAD_SPARKS, 'FxSparks'), (QUAD_EMBERS, 'FxEmbers')):
        for k in range(3):
            angle = math.pi * k / 3
            quad(FX_CENTRE, Vector((math.cos(angle), math.sin(angle), 0)), z, FX_SIZE, quadrant, bone)
    bm.to_mesh(fx_mesh)
    bm.free()
    fx = bpy.data.objects.new(lod['name'] + '_fx', fx_mesh)
    bpy.context.collection.objects.link(fx)
    apply_groups(fx, groups)
    return flame, fx


def cage_weights(height, heights):
    position = (height - heights[0]) / (heights[-1] - heights[0]) * CAGE_BONES - 0.5
    position = min(max(position, 0.0), CAGE_BONES - 1.0)
    index = min(int(position), CAGE_BONES - 2)
    f = position - index
    return [(f'CageW{index + 1}', 1.0 - f), (f'CageW{index + 2}', f)]


def apply_groups(obj, groups):
    made = {}
    for vertex, weights in enumerate(groups):
        for bone, value in weights:
            if bone not in made:
                made[bone] = obj.vertex_groups.new(name=bone)
            made[bone].add([vertex], value, 'REPLACE')


# -------------------------------------------------------------------------------------------------- materials
def blend_material(name, image_name, scroll_note):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(os.path.join(TEXTURES, image_name))
    material.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    material.node_tree.links.new(texture.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 1.0
    # Preview only (eevee review renders): the runtime material is set by finish_glb.py.
    bsdf.inputs['Emission Color'].default_value = (1, 1, 1, 1)
    material.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 1.0
    material['note'] = scroll_note
    return material


# ------------------------------------------------------------------------------------------------------ clips
def bump(t, start, end):
    if t <= start or t >= end:
        return 0.0
    return math.sin(math.pi * (t - start) / (end - start))


def ramp(t, start, end):
    """0 before start, 1 after end, smoothstep between."""
    if t <= start:
        return 0.0
    if t >= end:
        return 1.0
    x = (t - start) / (end - start)
    return x * x * (3 - 2 * x)


def noise(*values):
    return math.sin(sum(v * k for v, k in zip(values, (12.9898, 78.233, 37.719))) * 43758.5453) % 1.0


def key_bone(pb, frame, location=None, rotation=None, scale=None):
    if location is not None:
        pb.location = location
        pb.keyframe_insert('location', frame=frame)
    if rotation is not None:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = rotation
        pb.keyframe_insert('rotation_euler', frame=frame)
    if scale is not None:
        pb.scale = scale
        pb.keyframe_insert('scale', frame=frame)


def compose(rig, name, figure_action, seconds, shape):
    """A clip: the figure action's keys plus keys on Root, the cage, the bursts and the fx bones from shape(t, s)
    (t = 0..1 over the clip, s = seconds). shape returns any of: lean (radians), bob (units), size (Root),
    widths (per cage bone), sway (radians), bursts ((left, right) scale), star, sparks, embers (+ _twist), figure
    (Hips scale), cage_size (Cage1 uniform scale: the whole cage grows from its tip; height changes go here, never on
    the leaf width bones, whose blended stretch would kink the cage). Missing parts are at rest (bursts and fx hidden)."""
    if name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[name])
    action = figure_action.copy()
    action.name = name
    action.use_fake_user = True
    assign(rig, action)
    frames = int(round(seconds * FPS))
    pose = rig.pose.bones
    for frame in range(frames + 1):
        s = frame / FPS
        t = frame / frames
        values = shape(t, s)
        lean = values.get('lean', 0.0)
        bob = values.get('bob', 0.0)
        size = values.get('size', 1.0)
        # Root: lean about LEAN_PIVOT (a turn about the bone's head, moved so the pivot stays put). Bone space:
        # Y is up and Z is world -Y, so +X tilts the top forward.
        pivot = Vector((0.0, LEAN_PIVOT, 0.0))
        turned = Matrix.Rotation(lean, 3, 'X') @ pivot
        key_bone(pose['Root'], frame, location=(pivot - turned) + Vector((0.0, bob, 0.0)),
                 rotation=(lean, 0.0, 0.0), scale=(size, size, size))
        widths = values.get('widths', [1.0] * CAGE_BONES)
        sway = values.get('sway', [0.0] * CAGE_BONES)
        cage_size = values.get('cage_size', 1.0)
        for index in range(CAGE_BONES):
            sx, sz = sway[index] if isinstance(sway[index], tuple) else (sway[index], 0.0)
            key_bone(pose[f'Cage{index + 1}'], frame, rotation=(sx, 0.0, sz),
                     scale=(cage_size,) * 3 if index == 0 else (1.0, 1.0, 1.0))
            w = widths[index]
            key_bone(pose[f'CageW{index + 1}'], frame, scale=(w, 1.0, w))
        bursts = values.get('bursts', (HIDDEN, HIDDEN))
        for side, value in zip(('L', 'R'), bursts):
            spin = 2 * math.pi * noise(frame, 1.0 if side == 'L' else 2.0, 5.0)
            key_bone(pose[f'Burst{side}'], frame, rotation=(spin * 0.3, spin, spin * 0.2),
                     scale=(value, value, value))
        for bone, key in (('FxStar', 'star'), ('FxSparks', 'sparks'), ('FxEmbers', 'embers')):
            value = values.get(key, HIDDEN)
            twist = values.get(key + '_twist', 0.0)
            key_bone(pose[bone], frame, rotation=(0.0, twist, 0.0), scale=(value, value, value))
        # Keyed in every clip: an unkeyed channel would keep (and export) the value the previous clip left.
        figure = values.get('figure', 1.0)
        key_bone(pose['Hips'], frame, scale=(figure, figure, figure))
    for curve in action_curves(action):
        if curve.data_path.startswith('pose.bones["Burst') or curve.data_path.startswith('pose.bones["Fx'):
            if curve.data_path.endswith('rotation_euler'):
                for point in curve.keyframe_points:
                    point.interpolation = 'CONSTANT'
    action.frame_range = (0, frames)
    action.use_frame_range = True
    return action


def flicker(t, cycles, amplitude):
    """Per-bone width breathing and sway, periodic over the clip (whole cycles), later bones lagging."""
    phase = 2 * math.pi * cycles * t
    widths = [1.0 + amplitude * math.sin(phase + 0.9 * i) + 0.5 * amplitude * math.sin(2 * phase + 1.7 * i)
              for i in range(CAGE_BONES)]
    sway = [(0.02 * math.sin(phase + 0.8 * i), 0.02 * math.sin(phase + 1.1 * i + 1.0)) for i in range(CAGE_BONES)]
    return widths, sway


def standing(t, s):
    widths, sway = flicker(t, 3, 0.035)
    return {'widths': widths, 'sway': sway, 'bob': 0.03 * math.sin(2 * math.pi * 2 * t)}


def walking(t, s):
    values = standing(t, s)
    values['lean'] = LEAN
    return values


ATTACK_SECONDS = 34 / FPS
IMPACT = 0.75


def attack(t, s):
    """Library area attack (hands gather 0-0.5 s, burst apart at about 0.65 s, widest 1.05 s): the hand bursts
    grow as the hands part and crackle while they are out (native frames b-d); the cage flares round the
    shoulders."""
    widths, sway = flicker(t, 1, 0.03)
    grow = ramp(s, 0.5, 0.72) * (1.0 - ramp(s, 1.1, 1.3))
    bursts = []
    for side in range(2):
        jitter = 0.85 + 0.3 * noise(round(s * FPS), side, 9.0)
        bursts.append(max(grow * jitter, HIDDEN) if grow > 0.01 else HIDDEN)
    flare = bump(s, 0.5, 1.35)
    widths = [w * (1.0 + flare * (0.1 + 0.2 * (i in (3, 4)))) for i, w in enumerate(widths)]
    return {'widths': widths, 'sway': sway, 'bursts': tuple(bursts)}


def hit(t, s):
    """The cage pinches and shortens (native wince frames) and recovers within the native 0.75 s."""
    widths, sway = flicker(t, 1, 0.03)
    pinch = bump(min(s / 0.6, 1.0), 0.0, 1.0)
    return {'widths': [w * (1.0 - 0.2 * pinch) for w in widths], 'sway': sway, 'cage_size': 1.0 - 0.08 * pinch}


DEATH_SECONDS = 0.95


def death(t, s):
    """Native death: the cage swells round (a), tears outward (b, c) and is gone; the figure, flung back by the
    library clip, shrinks inside it; a star flashes at the chest (c-e), sparks fly out (d, e) and embers drift
    (f)."""
    swell = ramp(s, 0.0, 0.2)
    burst = ramp(s, 0.2, 0.4)
    gone = s >= 0.4
    widths = [HIDDEN if gone else (1.0 + 0.3 * swell + 0.9 * burst) * (1.0 + 0.15 * math.sin(i * 1.3))
              for i in range(CAGE_BONES)]
    # Gone: the whole cage scales away (zero width alone left a visible line of zero-width faces).
    values = {'widths': widths, 'cage_size': HIDDEN if gone else 1.0 + 0.08 * swell + 0.3 * burst,
              'figure': max(1.0 - ramp(s, 0.22, 0.38), HIDDEN)}
    if 0.25 <= s < 0.8:
        values['star'] = max(0.25 + 0.75 * ramp(s, 0.25, 0.42) - 0.6 * ramp(s, 0.5, 0.78), HIDDEN)
        values['star_twist'] = 0.3 * noise(round(s * FPS), 3.0, 1.0)
    if 0.36 <= s < 0.66:
        values['sparks'] = 0.6 + 0.55 * ramp(s, 0.36, 0.62)
        values['sparks_twist'] = 0.25 * noise(round(s * FPS), 4.0, 1.0)
    if 0.6 <= s < 0.92:
        values['embers'] = 1.0 + 0.3 * ramp(s, 0.6, 0.92)
    return values


def dead(t, s):
    return {'widths': [HIDDEN] * CAGE_BONES, 'cage_size': HIDDEN, 'figure': HIDDEN}


# ------------------------------------------------------------------------------------------------------- main
def main():
    scene = bpy.context.scene
    scene.render.fps = FPS
    rig = bpy.data.objects['FireElemental_Rig']
    body = bpy.data.objects['FireElemental_Body']
    rig.animation_data_create()
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix()
    heights = extend_rig(rig)
    body_material = bake_body_texture(body)
    flame_material = blend_material('FireElemental_Flame', 'fie1_flame.png', 'uv scroll')
    fringe_material = blend_material('FireElemental_Fringe', 'fie1_fringe.png', 'uv scroll')
    fx_material = blend_material('FireElemental_Fx', 'fie1_fx.png', 'static')
    materials = [body_material, flame_material, fringe_material, fx_material]
    objects = []
    for lod in LODS:
        lod_figure = lod_body(body, lod['body'], lod['name'])
        flame, fx = build_parts(lod, rig, heights)
        fins = build_fins(lod, heights)
        # Same slot list everywhere, so joining keeps the primitive order body, flame, fringe, fx.
        for part, index in ((lod_figure, 0), (flame, 1), (fins, 2), (fx, 3)):
            part.data.materials.clear()
            for material in materials:
                part.data.materials.append(material)
            for polygon in part.data.polygons:
                polygon.material_index = index
        for obj in bpy.context.scene.objects:
            obj.select_set(obj in (lod_figure, flame, fins, fx))
        bpy.context.view_layer.objects.active = lod_figure
        bpy.ops.object.join()
        for modifier in [m for m in lod_figure.modifiers if m.type == 'ARMATURE']:
            lod_figure.modifiers.remove(modifier)
        lod_figure.parent = rig
        modifier = lod_figure.modifiers.new('Armature', 'ARMATURE')
        modifier.object = rig
        objects.append(lod_figure)
    bpy.data.objects.remove(body, do_unlink=True)
    # The retargeted figure clips (retarget.py) become the sources of the composed clips of the same role.
    figure = {}
    for name in ('Floating', 'Attack', 'Hit', 'Death'):
        figure[name] = bpy.data.actions[name]
        figure[name].name = 'Figure' + name
    floating = figure['Floating']
    seconds = (floating.frame_range[1] - floating.frame_range[0]) / FPS
    compose(rig, 'Standing', floating, seconds, standing)
    compose(rig, 'Walking', floating, seconds, walking)
    compose(rig, 'Attack', figure['Attack'], ATTACK_SECONDS, attack)
    compose(rig, 'Hit', figure['Hit'], 23 / FPS, hit)
    compose(rig, 'Death', figure['Death'], DEATH_SECONDS, death)
    compose(rig, 'Dead', floating, 1.0, dead)
    for action in bpy.data.actions:
        if action.name not in ('Standing', 'Walking', 'Attack', 'Hit', 'Death', 'Dead'):
            bpy.data.actions.remove(action)
    assign(rig, bpy.data.actions['Standing'])
    scene.frame_set(0)
    os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'fie1.blend'))
    for obj in bpy.data.objects:
        obj.select_set(obj in objects or obj == rig)
    bpy.context.view_layer.objects.active = rig
    out = os.path.join(HERE, 'export', 'mm6_fie1_raw.glb')
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                              export_frame_step=1, export_skins=True, export_all_influences=False,
                              export_attributes=False, export_morph=False, export_image_format='AUTO',
                              export_reset_pose_bones=True, export_anim_slide_to_zero=True)
    print('EXPORTED', out, [(o.name, sum(len(p.vertices) - 2 for p in o.data.polygons)) for o in objects])


main()
