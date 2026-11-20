"""Shared Blender helpers of the MM7 fire batch: the MM6 props library (../../../mm6_new_sorpigal_3d/props/scripts/
props_lib.py, imported read only) with this batch's textures (textures/), COLOR_0 tints toward measured native
colours, flame cards on the shared flame flipbooks, glow materials and the LOD build-and-export loop.
Lengths are native map units (u() converts to Blender metres, 81.7 units per metre)."""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
HERE = os.path.dirname(SCRIPTS)
DECORATIONS = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(DECORATIONS, 'mm6_new_sorpigal_3d', 'props', 'scripts'))
import props_lib as pl  # noqa: E402

TEXTURES = os.path.join(HERE, 'textures')
UNITS_PER_METRE = 81.7
# Flame flipbooks (16 x 4 frames of the CC0 Unity Labs Flame02, a seamless 64-frame loop at 30 fps): the MM torch
# orange of the MM6 project and the shared coloured recolours. Texture v of the flame's base and of its tip in a
# frame (../../../mm6_dungeons_3d/fire/README.md, measured on flame02; the recolours keep its alpha).
FLAMES = {'orange': (os.path.join(DECORATIONS, 'mm6_dungeons_3d', 'textures'), 'flame02'),
          'blue': (os.path.join(DECORATIONS, 'shared_flames'), 'flame02_blue'),
          'white': (os.path.join(DECORATIONS, 'shared_flames'), 'flame02_white')}
FLAME_V = (0.023, 0.70)
with open(os.path.join(TEXTURES, 'means.json')) as handle:
    MEANS = json.load(handle)
TEXTURE_OF = {}


def u(value):
    return value / UNITS_PER_METRE


def material(name, texture, alpha=False, extras=None, folder=TEXTURES):
    TEXTURE_OF[name] = texture
    saved = pl.TEX
    pl.TEX = folder
    try:
        return pl.material(name, texture, alpha=alpha, extras=extras)
    finally:
        pl.TEX = saved


def set_emission(m, emission):
    """Constant emission (glTF emissiveFactor) from an sRGB colour; the engine adds it after lighting."""
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Emission Color'].default_value = tuple(linear(c) for c in emission) + (1.0,)
    bsdf.inputs['Emission Strength'].default_value = 1.0


def glow_material(name, texture, emission, pulse=None, extras=None):
    """A lit PBR material that also glows (constant emission), optionally pulsing per placement
    (openyamm_pulse [amplitude, period seconds])."""
    extras = dict(extras or {})
    if pulse:
        extras['openyamm_pulse'] = list(pulse)
    m = material(name, texture, extras=extras)
    set_emission(m, emission)
    return m


def flame_material(name, colour):
    """Unlit blended camera-facing card on a flame flipbook (finish.py FLAME)."""
    folder, texture = FLAMES[colour]
    return material(name, texture, alpha=True, folder=folder,
                    extras={'openyamm_billboard': True, 'openyamm_flipbook': [16, 4, 30], 'openyamm_specular': 0.0})


def flame_card_material(name, colour):
    """An off-axis flame card: the same flipbook, turned about its own vertical centre (openyamm_billboard "card");
    each card needs its own material, so that it is its own primitive."""
    folder, texture = FLAMES[colour]
    return material(name, texture, alpha=True, folder=folder,
                    extras={'openyamm_billboard': 'card', 'openyamm_flipbook': [16, 4, 30], 'openyamm_specular': 0.0})


def halo_material(name, card=False):
    """Additive soft glow (finish.py HALO: BLEND, unlit, double-sided): colour times alpha is added and fades with
    fog. Its colour and strength come from COLOR_0 (tint ('mul', ...)) or a finish factor."""
    return material(name, 'halo', alpha=True, extras={'openyamm_billboard': 'card' if card else True,
                                                      'openyamm_additive': True, 'openyamm_specular': 0.0})


def glow_card(name, mat, centre_z, width, height, x=0.0, y=0.0):
    """A camera-facing glow quad centred at (x, y, centre_z) in the model's x/up plane (units)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    corners = ((x - width / 2, centre_z - height / 2), (x + width / 2, centre_z - height / 2),
               (x + width / 2, centre_z + height / 2), (x - width / 2, centre_z + height / 2))
    face = bm.faces.new([bm.verts.new((u(cx), u(y), u(cz))) for cx, cz in corners])
    for loop, st in zip(face.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = st
    return pl.to_object(name, bm, mat, smooth=False)


def review_additive(m, factor=(1.0, 1.0, 1.0)):
    """Review renders only: rebuild an imported additive material as transparent + emission (base texture x COLOR_0 x
    factor x alpha), the engine's additive blend."""
    nt = m.node_tree
    image = next(n.image for n in nt.nodes if n.type == 'TEX_IMAGE')
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = image
    attribute = nt.nodes.new('ShaderNodeVertexColor')
    tint = nt.nodes.new('ShaderNodeMix')
    tint.data_type = 'RGBA'
    tint.blend_type = 'MULTIPLY'
    tint.inputs['Factor'].default_value = 1.0
    nt.links.new(tex.outputs['Color'], tint.inputs['A'])
    nt.links.new(attribute.outputs['Color'], tint.inputs['B'])
    scale = nt.nodes.new('ShaderNodeVectorMath')
    scale.operation = 'MULTIPLY'
    nt.links.new(tint.outputs['Result'], scale.inputs[0])
    scale.inputs[1].default_value = tuple(factor)
    alpha = nt.nodes.new('ShaderNodeVectorMath')
    alpha.operation = 'SCALE'
    nt.links.new(scale.outputs['Vector'], alpha.inputs[0])
    nt.links.new(tex.outputs['Alpha'], alpha.inputs['Scale'])
    emit = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(alpha.outputs['Vector'], emit.inputs['Color'])
    add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(nt.nodes.new('ShaderNodeBsdfTransparent').outputs[0], add.inputs[0])
    nt.links.new(emit.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'


def linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mix(a, b, t):
    t = min(1.0, max(0.0, t))
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def stops(points, z):
    """Piecewise-linear sRGB colour over height: points [(z units, (r, g, b)), ...] bottom to top."""
    if z <= points[0][0]:
        return points[0][1]
    for (z0, c0), (z1, c1) in zip(points, points[1:]):
        if z <= z1:
            return mix(c0, c1, (z - z0) / (z1 - z0))
    return points[-1][1]


def tint(obj, colours):
    """Multiply each vertex's occlusion colour by linear(target sRGB) / linear(texture mean) of its material.
    colours: material name -> sRGB tuple, a callable (co in units, normal) -> sRGB tuple, or ('scale', s) / ('mul', (r, g, b))
    for plain linear multipliers. Factors above one are allowed up to 1.6 (COLOR_0 is a float attribute; the engine multiplies)."""
    me = obj.data
    names = [m.name for m in me.materials]
    attr = me.color_attributes['Color']
    owner = {}
    for polygon in me.polygons:
        for index in polygon.vertices:
            owner[index] = names[polygon.material_index]
    for index, name in owner.items():
        target = colours.get(name)
        if target is None:
            continue
        vertex = me.vertices[index]
        if callable(target):
            target = target(vertex.co * UNITS_PER_METRE, vertex.normal)
        if target[0] == 'scale':
            factor = [target[1]] * 3
        elif target[0] == 'mul':
            factor = list(target[1])
        else:
            mean = MEANS[TEXTURE_OF[name]]
            factor = [min(1.6, linear(value) / mean[channel]) for channel, value in enumerate(target)]
        c = attr.data[index].color
        attr.data[index].color = (c[0] * factor[0], c[1] * factor[1], c[2] * factor[2], c[3])


def flame_card(name, mat, base_z, tip_z, width, x=0.0, mirrored=False, y=0.0, shift=0):
    """A card whose flipbook flame base sits at base_z and whose tip reaches tip_z (units); the card ends at the tip,
    so the bounds do not rise above the sprite. The flame fills about 60 % of the width. y: depth offset (off-axis
    "card" billboards). shift: whole texture units added to u, so the flipbook shows a frame `shift` columns later
    (cards of one placement then do not flicker in step; the sampler repeats)."""
    v_base, v_tip = FLAME_V
    per_v = (tip_z - base_z) / (v_tip - v_base)
    z0 = base_z - v_base * per_v
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    corners = ((u(x - width / 2), u(y), u(z0)), (u(x + width / 2), u(y), u(z0)), (u(x + width / 2), u(y), u(tip_z)),
               (u(x - width / 2), u(y), u(tip_z)))
    face = bm.faces.new([bm.verts.new(c) for c in corners])
    for loop, (s, t) in zip(face.loops, ((0, 0), (1, 0), (1, v_tip), (0, v_tip))):
        loop[uv].uv = ((1 - s if mirrored else s) + shift, t)
    return pl.to_object(name, bm, mat, smooth=False)


def lathe(name, profile, segments, mat, u_repeat=1.0, v_scale=1.0, smooth=True, cap_top=False, cap_bottom=False):
    """pl.lathe on a profile in units [(radius, z), ...]; v_scale per metre."""
    return pl.lathe(name, [(u(r), u(z)) for r, z in profile], segments, mat, u_repeat=u_repeat, v_scale=v_scale,
                    smooth=smooth, cap_top=cap_top, cap_bottom=cap_bottom)


def tube(name, a, b, ra, rb, sides, mat, v_scale=2.0, caps=True, u_repeat=1.0):
    return pl.tube(name, [u(c) for c in a], [u(c) for c in b], u(ra), u(rb), sides, mat, v_scale=v_scale, caps=caps,
                   u_repeat=u_repeat)


def torus(name, radius, minor, z, segments, sides, mat, u_repeat=2.0, squash=1.0):
    """A ring (lathe of a circle) of major radius `radius`, minor radius `minor` at height z (units); squash scales
    its height."""
    profile = []
    for j in range(sides + 1):
        a = -math.pi / 2 + 2 * math.pi * j / sides
        profile.append((radius + minor * math.cos(a), z + minor * math.sin(a) * squash))
    return lathe(name, profile, segments, mat, u_repeat=u_repeat, v_scale=4.0)


def apply(objects):
    for obj in objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return objects


def merge_materials(obj, merge):
    """Move the faces of each material in merge (name -> target name) onto the target's slot and drop the slot."""
    for source, target in merge.items():
        names = [m.name for m in obj.data.materials]
        if source not in names or target not in names:
            continue
        s, t = names.index(source), names.index(target)
        for polygon in obj.data.polygons:
            if polygon.material_index == s:
                polygon.material_index = t
        obj.active_material_index = s
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.material_slot_remove()


def order_materials(obj, last):
    """Move the named material slots to the end (blended cards draw after the opaque parts, in glTF order)."""
    for name in last:
        names = [m.name for m in obj.data.materials]
        if name not in names:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        obj.active_material_index = names.index(name)
        for _ in range(len(names) - 1 - names.index(name)):
            bpy.ops.object.material_slot_move(direction='DOWN')


def build_lods(base_name, prop, build, colours, rays=(32, 20, 12), distance=20.0, strength=0.5, levels=3,
               merge=None, alpha=None, last=(), sharp=38):
    """build(level) -> (solid objects, white objects (flame cards, glows: no occlusion)); occlusion on the solids,
    tints from colours, merged materials, one joined object per LOD (solid edges sharper than `sharp` degrees split); saves work/<prop>.blend and exports
    work/<prop>_export.glb. alpha: optional per-vertex callable (co metres) -> COLOR_0 alpha."""
    lods = []
    for level in range(levels):
        solids, whites = build(level)
        solid = pl.join(f'solid{level}', solids)
        if sharp:
            solid.data.set_sharp_from_angle(angle=math.radians(sharp))
        occlusion = pl.vertex_occlusion(solid, rays=rays[level], distance=u(distance), strength=strength,
                                        floor=False, alpha=alpha)
        tint(solid, colours)
        parts = [solid]
        for obj in whites:
            pl.white_colour(obj, alpha=alpha)
            tint(obj, colours)
            parts.append(obj)
        name = base_name if level == 0 else f'{base_name}_LOD{level}'
        obj = pl.join(name, parts)
        merge_materials(obj, merge or {})
        order_materials(obj, last)
        print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(occlusion, 3))
        lods.append(obj)
    work = os.path.join(HERE, 'work')
    os.makedirs(work, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, f'{prop}.blend'))
    pl.export(lods, os.path.join(work, f'{prop}_export.glb'))
    return lods
