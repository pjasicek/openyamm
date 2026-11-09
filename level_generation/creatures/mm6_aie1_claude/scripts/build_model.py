"""MM6 air elemental (aie1): wind shells revolved from the restored standing silhouette, thin dust rings and lightning
shells outside them, a vertical bone chain, three LOD meshes and the Standing/Attack/Hit/Death/Dead clips. Run under
Blender:

    blender --background --factory-startup --python scripts/build_model.py

Units: 1 Blender unit = 100 native logical pixels, origin at the sprite's ground pivot (actors.yml scale 59.9991 =
100 x the native frame scale). Forward is -Y (actors.yml yaw_offset -pi/2). Writes work/aie1.blend and
export/mm6_aie1_raw.glb (finish_glb.py wires the LODs and sets the runtime material and tiers).

Blending: the material is single-sided and draws in index order (the engine keeps a blended primitive's authored
triangle order), so each mesh's faces go back to front for any outside view: the inner sides from the outermost layer
in (lightning shells, dust rings, outer shell, core), then the outer sides from the core out. Backface culling keeps
only the far half of each inner side and the near half of each outer side.

Motion: the spin is the material's texture scroll (finish_glb.py), so it stays continuous across clips. The funnel
bones only turn (sway, lean) and Root only moves and scales uniformly; the width of the wind is a non-uniform scale on
leaf Wind bones (one per funnel bone, deforming the wind and dust), so no scaled bone has children and the chain never
shears. Each lightning shell has its own bone per funnel bone; scaled to almost
nothing it collapses onto the axis (hidden), and in the attack it grows out from the axis with stepped twists that
make the discharge crackle.
"""
import json
import math
import os

import bmesh
import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE = json.load(open(os.path.join(HERE, 'textures', 'aie1_profile.json')))
# Native actions are six 125 ms frames: 24 fps gives whole frames for every 750 ms clip.
FPS = 24
BONES = 6
HIDDEN = 0.001
# Bone k of the chain leans by lean * k / LEAN_SPREAD, so the top tilts by about lean in all.
LEAN_SPREAD = sum(range(6))

LODS = [
    {'name': 'AirElemental', 'segments': 24, 'rings': 12, 'dust': 14, 'dust_segments': 16, 'bolts': 3,
     'bolt_segments': 16, 'bolt_rings': 8},
    {'name': 'AirElemental_LOD1', 'segments': 16, 'rings': 9, 'dust': 10, 'dust_segments': 12, 'bolts': 2,
     'bolt_segments': 12, 'bolt_rings': 6},
    {'name': 'AirElemental_LOD2', 'segments': 10, 'rings': 6, 'dust': 6, 'dust_segments': 8, 'bolts': 1,
     'bolt_segments': 8, 'bolt_rings': 5},
]
BOLT_SHELLS = 3

# Profile from the second row (the first is the ragged rim's sparse tips), in Blender units.
rows = list(zip(PROFILE['height_px'], PROFILE['radius_px'], PROFILE['offset_px']))[1:]


def profile_at(t):
    """Height, radius and sideways axis offset at t (0 = top rim, 1 = tip), interpolated."""
    position = t * (len(rows) - 1)
    index = min(int(position), len(rows) - 2)
    f = position - index
    a, b = rows[index], rows[index + 1]
    return [(a[k] * (1 - f) + b[k] * f) / 100.0 for k in range(3)]


QUARTER = 0.25
BAND_PAD = 6 / 2048.0
BODY_BAND, OUTER_BAND, DUST_BAND, BOLT_BAND = [(QUARTER * k, QUARTER * (k + 1)) for k in range(4)]
SHELLS = [
    # name, radius scale, extra radius, texture u repeats around, texture v band
    ('outer', 1.12, 0.03, 2.0, OUTER_BAND),
    ('core', 0.9, 0.0, 1.0, BODY_BAND),
]
DUST_HEIGHT = 0.05
# The bolt texture is unwrapped at 1.35 x the silhouette radius (make_texture.py LIGHTNING_RADIUS).
BOLT_RADII = [1.32, 1.4, 1.48]


def band_v(band, f):
    return band[0] + BAND_PAD + (band[1] - band[0] - 2 * BAND_PAD) * f


def shell_rows(shell, rings):
    """(height, radius, axis offset, texture v) per ring of a shell, top rim to tip."""
    name, scale, extra, _repeats, band = shell
    rows_out = []
    for ring in range(rings):
        t = ring / (rings - 1)
        height, radius, offset = profile_at(t)
        # The outer wind flares a little more at the rim.
        radius = radius * scale + extra * (1.0 - 0.6 * t)
        if name == 'outer':
            height += 0.04 * (1.0 - t)
        rows_out.append((height, max(radius, 0.02), offset, band_v(band, t)))
    return rows_out


def bolt_rows(shell, rings):
    rows_out = []
    for ring in range(rings):
        t = ring / (rings - 1)
        height, radius, offset = profile_at(t)
        rows_out.append((height, max(radius * BOLT_RADII[shell] + 0.01, 0.03), offset, band_v(BOLT_BAND, t)))
    return rows_out


def dust_layers(count):
    """One two-row strip per dust ring: (rows, u repeats, u phase), the widest rings first. Golden-ratio sequences
    spread heights, radii and texture slices without visible order, the same for every LOD."""
    layers = []
    for index in range(count):
        jitter = (index * 0.618034) % 1.0
        t = 0.04 + 0.84 * (index + 0.5 * jitter) / count
        height, radius, offset = profile_at(t)
        radius = radius * (1.15 + 0.25 * ((index * 0.381966 + 0.2) % 1.0)) + 0.02
        slice_start = 0.85 * ((index * 0.7548777) % 1.0)
        rows_out = [(height + DUST_HEIGHT / 2, radius, offset, band_v(DUST_BAND, slice_start)),
                    (height - DUST_HEIGHT / 2, radius * 0.97, offset, band_v(DUST_BAND, slice_start + 0.1))]
        layers.append((rows_out, 3.0, jitter))
    layers.sort(key=lambda layer: -layer[0][0][1])
    return layers


def build_mesh(lod):
    """One LOD mesh. Returns the object and, per vertex, its lightning shell (0 = funnel, k = bolt shell k)."""
    mesh = bpy.data.meshes.new(lod['name'])
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    shell_of_vertex = []

    def strip(rows_in, segments, repeats, phase, bolt, inward):
        """A revolved strip; each side has its own vertices (its own normals: the inner side faces the axis)."""
        grid = []
        for height, radius, offset, _v in rows_in:
            grid.append([bm.verts.new((offset + radius * math.cos(2 * math.pi * k / segments),
                                       radius * math.sin(2 * math.pi * k / segments), height))
                         for k in range(segments)])
            shell_of_vertex.extend([bolt] * segments)
        for ring in range(len(rows_in) - 1):
            v0, v1 = rows_in[ring][3], rows_in[ring + 1][3]
            for segment in range(segments):
                nxt = (segment + 1) % segments
                quad = [grid[ring][segment], grid[ring + 1][segment], grid[ring + 1][nxt], grid[ring][nxt]]
                u0, u1 = phase + repeats * segment / segments, phase + repeats * (segment + 1) / segments
                uvs = [(u0, v0), (u0, v1), (u1, v1), (u1, v0)]
                if inward:
                    quad, uvs = quad[::-1], uvs[::-1]
                face = bm.faces.new(quad)
                face.smooth = True
                for loop, (u, v) in zip(face.loops, uvs):
                    # glTF v runs down the image; Blender's runs up.
                    loop[uv].uv = (u, 1.0 - v)

    # Outermost first: (rows, segments, u repeats, u phase, bolt shell). The bolt shells repeat the texture once,
    # a third of a turn apart, the middle one mirrored (negative repeats) so no two show the same branches.
    layers = [(bolt_rows(shell, lod['bolt_rings']), lod['bolt_segments'], -1.0 if shell == 1 else 1.0,
               shell / 3.0, shell + 1) for shell in reversed(range(lod['bolts']))]
    layers += [(rows_in, lod['dust_segments'], repeats, phase, 0)
               for rows_in, repeats, phase in dust_layers(lod['dust'])]
    layers += [(shell_rows(shell, lod['rings']), lod['segments'], shell[3], 0.0, 0) for shell in SHELLS]
    for layer in layers:
        strip(*layer, inward=True)
    for layer in reversed(layers):
        strip(*layer, inward=False)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(lod['name'], mesh)
    bpy.context.collection.objects.link(obj)
    return obj, shell_of_vertex


def build_rig():
    arm = bpy.data.armatures.new('AirElemental_Rig')
    rig = bpy.data.objects.new('AirElemental_Rig', arm)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    tip_height, _r, _o = profile_at(1.0)
    top_height, _r, _o = profile_at(0.0)
    root = arm.edit_bones.new('Root')
    root.head, root.tail = (0, 0, 0), (0, 0.0, tip_height)
    parent = root
    heights = [tip_height + (top_height - tip_height) * i / BONES for i in range(BONES + 1)]
    funnel = []
    for index in range(BONES):
        bone = arm.edit_bones.new(f'Funnel{index + 1}')
        bone.head, bone.tail = (0, 0, heights[index]), (0, 0, heights[index + 1])
        bone.parent = parent
        bone.use_connect = index > 0
        parent = bone
        funnel.append(bone)
    for index in range(BONES):
        bone = arm.edit_bones.new(f'Wind{index + 1}')
        bone.head, bone.tail = funnel[index].head.copy(), funnel[index].tail.copy()
        bone.parent = funnel[index]
    for shell in range(BOLT_SHELLS):
        for index in range(BONES):
            bone = arm.edit_bones.new(f'Bolt{shell + 1}_{index + 1}')
            bone.head, bone.tail = funnel[index].head.copy(), funnel[index].tail.copy()
            bone.parent = funnel[index]
    bpy.ops.object.mode_set(mode='OBJECT')
    return rig, heights


def weight(obj, shell_of_vertex, rig, heights):
    """Linear weights along the chain by height: each vertex between its two nearest bone joints, on the Wind bones
    or on its lightning shell's bones."""
    groups = {}
    for vertex in obj.data.vertices:
        prefix = 'Wind' if shell_of_vertex[vertex.index] == 0 else f'Bolt{shell_of_vertex[vertex.index]}_'
        position = (vertex.co.z - heights[0]) / (heights[-1] - heights[0]) * BONES - 0.5
        position = min(max(position, 0.0), BONES - 1.0)
        index = min(int(position), BONES - 2)
        f = position - index
        for bone_index, value in ((index, 1.0 - f), (index + 1, f)):
            name = f'{prefix}{bone_index + 1}'
            if name not in groups:
                groups[name] = obj.vertex_groups.new(name=name)
            groups[name].add([vertex.index], value, 'REPLACE')
    obj.parent = rig
    modifier = obj.modifiers.new('Armature', 'ARMATURE')
    modifier.object = rig


def bump(t, start, end):
    """0 outside [start, end], a smooth sine hump inside."""
    if t <= start or t >= end:
        return 0.0
    return math.sin(math.pi * (t - start) / (end - start))


def noise(*values):
    """Deterministic pseudo-random 0..1."""
    return math.sin(sum(v * k for v, k in zip(values, (12.9898, 78.233, 37.719))) * 43758.5453) % 1.0


# Pose channels are in bone space, and every bone points up: bone Y is the world vertical, bone X and Z the
# horizontal axes. A positive X rotation tilts a bone's tip toward bone Z, which is world -Y: forward.
def animate(rig, action_name, seconds, amplitude, shape=lambda t: {}, step=2):
    """Snaking sway: each joint swings on two slow sines, later joints lagging, so the funnel bends like a rope.
    shape(t) may return width (Wind bones), size (uniform Root scale), lean (forward tilt of the top, radians, spread
    over the chain) and bolts (one scale per lightning shell, absent = hidden)."""
    action = bpy.data.actions.new(action_name)
    rig.animation_data_create()
    rig.animation_data.action = action
    frames = int(round(seconds * FPS))
    root = rig.pose.bones['Root']
    for frame in range(0, frames + 1, step):
        t = frame / frames
        phase = 2 * math.pi * t
        values = shape(t)
        for index in range(BONES):
            bone = rig.pose.bones[f'Funnel{index + 1}']
            lag = 0.9 * index
            weight_up = 0.35 + 0.65 * index / (BONES - 1)
            bone.rotation_mode = 'XYZ'
            bone.rotation_euler = (amplitude * weight_up * math.sin(phase + lag)
                                   + values.get('lean', 0.0) * index / LEAN_SPREAD, 0.0,
                                   amplitude * weight_up * 0.7 * math.sin(2 * phase + 1.3 * lag + 0.8))
            bone.keyframe_insert('rotation_euler', frame=frame + 1)
        # The tip wanders over the ground.
        root.location = (0.04 * math.sin(phase + 0.4), 0.0, 0.03 * math.sin(2 * phase))
        root.keyframe_insert('location', frame=frame + 1)
        size = values.get('size', 1.0)
        root.scale = (size, size, size)
        root.keyframe_insert('scale', frame=frame + 1)
        width = values.get('width', 1.0)
        for index in range(BONES):
            bone = rig.pose.bones[f'Wind{index + 1}']
            bone.scale = (width, 1.0, width)
            bone.keyframe_insert('scale', frame=frame + 1)
        bolts = values.get('bolts', [])
        for shell in range(BOLT_SHELLS):
            scale = bolts[shell] if shell < len(bolts) else HIDDEN
            for index in range(BONES):
                bone = rig.pose.bones[f'Bolt{shell + 1}_{index + 1}']
                bone.rotation_mode = 'XYZ'
                # A new twist every key, held: the branches jump instead of turning.
                bone.rotation_euler = (0.0, 2 * math.pi * noise(frame, shell, 1.0), 0.0)
                bone.keyframe_insert('rotation_euler', frame=frame + 1)
                bone.scale = (scale, scale * (0.9 + 0.2 * noise(frame, shell, index)), scale)
                bone.keyframe_insert('scale', frame=frame + 1)
    for curve in action_curves(action):
        if curve.data_path.startswith('pose.bones["Bolt'):
            for point in curve.keyframe_points:
                point.interpolation = 'CONSTANT'
    action.use_fake_user = True
    return action


def action_curves(action):
    """F-curves of an action: layered actions (Blender 4.4+) keep them in channel bags."""
    if hasattr(action, 'layers') and action.layers:
        return [curve for layer in action.layers for strip in layer.strips for bag in strip.channelbags
                for curve in bag.fcurves]
    return list(action.fcurves)


def attack(t):
    """Native attack: the funnel gathers (a), the discharge builds through b-d, peaks at c and subsides (e, f).
    The bolt shells light one after another, each flickering off now and then; the funnel flares and leans in."""
    windows = [(0.14, 0.72), (0.25, 0.62), (0.3, 0.54)]
    bolts = []
    for shell, (start, end) in enumerate(windows):
        on = start < t < end and noise(t * 97.0, shell, 3.0) > 0.18
        bolts.append((0.75 + 0.35 * bump(t, start, end)) if on else HIDDEN)
    return {'width': 1.0 + 0.2 * bump(t, 0.12, 0.75) - 0.06 * bump(t, 0.0, 0.16),
            'lean': 0.25 * bump(t, 0.18, 0.7) - 0.08 * bump(t, 0.0, 0.18), 'bolts': bolts}


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    rig, heights = build_rig()
    objects = []
    for lod in LODS:
        obj, shell_of_vertex = build_mesh(lod)
        weight(obj, shell_of_vertex, rig, heights)
        objects.append(obj)
    animate(rig, 'Standing', 4.0, 0.06)
    animate(rig, 'Attack', 0.75, 0.08, attack, step=1)
    # Hit: the native frames pinch the funnel and let it recover; it recoils from the blow.
    animate(rig, 'Hit', 0.75, 0.10, lambda t: {'width': 1.0 - 0.42 * bump(min(t / 0.8, 1.0), 0.0, 1.0),
                                                'lean': -0.15 * bump(t, 0.0, 0.7)})
    # Death thins the funnel to nothing (the native frames break up and vanish); Dead holds it gone.
    animate(rig, 'Death', 0.75, 0.10, lambda t: {'width': max(1.0 - t ** 0.8, HIDDEN), 'size': 1.0 - 0.4 * t})
    animate(rig, 'Dead', 1.0, 0.0, lambda t: {'width': HIDDEN, 'size': 0.6})
    rig.animation_data.action = bpy.data.actions['Standing']
    scene.frame_set(1)
    material = bpy.data.materials.new('AirElemental_Wind')
    material.use_nodes = True
    nodes = material.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    image = bpy.data.images.load(os.path.join(HERE, 'textures', 'aie1_wind.png'))
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = image
    material.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
    material.node_tree.links.new(texture.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 1.0
    for obj in objects:
        obj.data.materials.append(material)
    os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'export'), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'aie1.blend'))
    for o in bpy.data.objects:
        o.select_set(o in objects or o == rig)
    bpy.context.view_layer.objects.active = rig
    out = os.path.join(HERE, 'export', 'mm6_aie1_raw.glb')
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                              export_frame_step=1, export_skins=True, export_all_influences=False,
                              export_attributes=False, export_morph=False, export_image_format='AUTO',
                              export_reset_pose_bones=True, export_anim_slide_to_zero=True)
    print('EXPORTED', out, [(o.name, len(o.data.polygons) * 2) for o in objects])


main()
