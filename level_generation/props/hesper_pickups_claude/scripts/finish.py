"""Finish the baked pickups (codex_texture.py bake: work/codex_tex/<design>_export.glb) into the models the stage
installs (hesper_stage/decorations.yml: work/export/<name>_export.glb), metres, origin at the centre of the base:

- every design scaled to its designs.json height_m;
- the two containers (FLUID) as one model in eight material variants: the painted fluid (red in the canister's
  paintings, green in the vat's) is found by its hue in the baked base colour (the region mask, review/masks/), and
  each of the seven colours recolours it through its own ramp of the painting's brightness and lights it with an
  emissive map of the same mask; the canister's empty variant turns the fluid into dark smoky glass with no glow.
  The vat's empty state is its own model (hes_serum_vat_empty: the torn membrane), so the vat has the seven colours.

    blender --background --python finish.py -- [design ...]
"""
import json
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'projectiles_claude',
                                'scripts'))
import projlib as pl  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAKED = os.path.join(HERE, 'work', 'codex_tex')
OUT = os.path.join(HERE, 'work', 'export')
MASKS = os.path.join(HERE, 'review', 'masks')
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))
# The seven colours (PICKUPS.md) at full strength; each ramp runs from a third of it in the fluid's shadows to it
# lifted toward white in the highlights.
COLOURS = {'red': (0.92, 0.07, 0.05), 'yellow': (0.95, 0.78, 0.1), 'blue': (0.1, 0.32, 1.0),
           'orange': (1.0, 0.42, 0.05), 'green': (0.24, 0.9, 0.1), 'purple': (0.58, 0.16, 0.95),
           'white': (0.9, 0.92, 0.97)}
# The painted fluid: its hue window (0-1), the least saturation and value of a fluid texel, and the variants.
FLUID = {'hes_stim_canister': {'hue': (0.94, 0.04), 'saturation': 0.5, 'value': 0.3, 'empty': True},
         'hes_serum_vat': {'hue': (0.17, 0.45), 'saturation': 0.4, 'value': 0.25, 'empty': False}}
EMISSION = 0.7


def hsv(rgb):
    high, low = rgb.max(-1), rgb.min(-1)
    delta = high - low
    hue = np.zeros_like(high)
    safe = np.where(delta > 1e-6, delta, 1)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.where(high == r, ((g - b) / safe) % 6, hue)
    hue = np.where(high == g, (b - r) / safe + 2, hue)
    hue = np.where(high == b, (r - g) / safe + 4, hue)
    hue = np.where(delta > 1e-6, hue / 6, 0)
    return hue, np.where(high > 1e-6, delta / np.where(high > 1e-6, high, 1), 0), high


def soften(mask, steps):
    for _ in range(steps):
        mask = (mask * 4 + np.roll(mask, 1, 0) + np.roll(mask, -1, 0) + np.roll(mask, 1, 1) + np.roll(mask, -1, 1)) / 8
    return mask


def fluid_mask(rgb, spec):
    hue, saturation, value = hsv(rgb)
    lo, hi = spec['hue']
    in_hue = (hue >= lo) | (hue <= hi) if lo > hi else (hue >= lo) & (hue <= hi)
    mask = (in_hue & (saturation >= spec['saturation']) & (value >= spec['value'])).astype(np.float32)
    # Drop specks (fewer than three fluid neighbours), then soften the edge by a texel.
    neighbours = sum(np.roll(np.roll(mask, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) - mask
    mask *= neighbours >= 3
    return np.clip(soften(mask, 1) * 1.5, 0, 1)


def image_pixels(image):
    width, height = image.size
    return np.array(image.pixels[:], np.float32).reshape(height, width, 4)


def new_image(name, rgb, colorspace='sRGB'):
    height, width = rgb.shape[:2]
    image = bpy.data.images.new(name, width, height, alpha=False)
    image.colorspace_settings.name = colorspace
    image.pixels[:] = np.concatenate([np.clip(rgb, 0, 1), np.ones((height, width, 1), np.float32)], -1).ravel()
    image.pack()
    return image


def load(design):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(BAKED, f'{design}_export.glb'))
    obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    zs = [(obj.matrix_world @ v.co).z for v in obj.data.vertices]
    scale = DESIGNS[design]['height_m'] / (max(zs) - min(zs))
    obj.scale = [s * scale for s in obj.scale]
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    zmin = min(v.co.z for v in obj.data.vertices)
    for v in obj.data.vertices:
        v.co.z -= zmin
    return obj


def variants(design, obj):
    spec = FLUID[design]
    material = obj.data.materials[0]
    nodes = material.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    base_node = bsdf.inputs['Base Color'].links[0].from_node
    pixels = image_pixels(base_node.image)
    rgb = pixels[..., :3]
    mask = fluid_mask(rgb, spec)
    os.makedirs(MASKS, exist_ok=True)
    new_image(f'{design}_mask', np.repeat(mask[..., None], 3, -1), 'Non-Color').save(
        filepath=os.path.join(MASKS, f'{design}_mask.png'))
    luminance = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    inside = mask > 0.5
    lo, hi = np.percentile(luminance[inside], [5, 95])
    t = np.clip((luminance - lo) / max(hi - lo, 1e-3), 0, 1)[..., None]
    emission_node = nodes.new('ShaderNodeTexImage')
    looks = dict(COLOURS)
    if spec['empty']:
        looks['empty'] = None
    for name, colour in looks.items():
        if colour is None:          # dark smoky glass, a faint grey-blue sheen in the painting's highlights
            fluid = np.array([0.04, 0.045, 0.055], np.float32) + t * np.array([0.1, 0.11, 0.13], np.float32)
        else:
            colour = np.array(colour, np.float32)
            fluid = colour * (0.33 + 0.67 * t)
            fluid = fluid + (1 - fluid) * np.clip((t - 0.75) / 0.25, 0, 1) * 0.45
        recoloured = rgb + (fluid - rgb) * mask[..., None]
        base_node.image = new_image(f'{design}_{name}_basecolor', recoloured)
        if colour is None:
            for link in list(bsdf.inputs['Emission Color'].links):
                material.node_tree.links.remove(link)
            bsdf.inputs['Emission Strength'].default_value = 0.0
        else:
            emission_node.image = new_image(f'{design}_{name}_emissive', fluid * mask[..., None] * EMISSION)
            material.node_tree.links.new(emission_node.outputs['Color'], bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = 1.0
        material.name = f'{design}_{name}'
        pl.export(obj, f'{design}_{name}')
    print('FLUID', design, 'mask texels', int(inside.sum()))


def main():
    names = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    pl.WORK = OUT
    os.makedirs(OUT, exist_ok=True)
    for design in names or [name for name in DESIGNS if os.path.exists(os.path.join(BAKED, f'{name}_export.glb'))]:
        obj = load(design)
        if design in FLUID:
            variants(design, obj)
        else:
            pl.export(obj, design)
    sys.stdout.flush()
    os._exit(0)


main()
