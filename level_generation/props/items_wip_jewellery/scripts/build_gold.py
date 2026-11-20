"""Gold heaps: every icon of the gold manifest -> work/gold/<icon>_export.glb, a heap of real coins.

The icons are paintings of coin heaps seen at an angle; projecting them onto a shape smeared the coins into streaks, so
the heap is built from coins instead: octagonal discs (radius 1 Blender unit, thickness 0.16) on a low mound, each
lying on the mound's slope with a random tilt and spin, their count from the icon's painted area; larger heaps get a
few short stacks, as the paintings show. Every coin shares one small texture (textures/gold_coin_*: an embossed face
with a raised rim, made here; no bottom face) and one gold material (metallic 0.7: fully metallic gold reflected only the hazy sky and read olive in game); COLOR_0 darkens coins low in the heap and varies each coin a
little. The mound under the coins (a dark gold dome) hides the gaps. Lowest point at 0, footprint centred; the
binding's length (the icon's width) sets the world size.
Usage: blender --background --python build_gold.py -- [icon ...]"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'projectiles_claude',
                                'scripts'))
import projlib as pl  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTURES = os.path.join(HERE, 'textures')
SIDES = 8
THICKNESS = 0.16
TEXTURE_SIZE = 256


def coin_textures():
    """textures/gold_coin_basecolor.png and _normal.png: the left square is the face (a disc), the right column the
    rim (a strip). The face: raised rim, a ring of beads, a raised centre boss with a cross; height -> normal."""
    size = TEXTURE_SIZE
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    u = (x + 0.5) / size * 2.0 - 1.0
    v = (y + 0.5) / size * 2.0 - 1.0
    r = np.hypot(u, v)
    angle = np.arctan2(v, u)
    height = np.zeros_like(r)
    height += np.clip((r - 0.82) / 0.06, 0, 1) * 1.0                       # rim
    beads = (np.cos(angle * 24) > 0.55) & (np.abs(r - 0.72) < 0.035)
    height += beads * 0.55
    height += np.clip((0.34 - r) / 0.08, 0, 1) * 0.6                       # boss
    cross = ((np.abs(u) < 0.05) | (np.abs(v) < 0.05)) & (r < 0.28)
    height += cross * 0.35
    height = np.where(r > 0.98, 0.6, height)
    gy, gx = np.gradient(height * 6.0)
    normal = np.stack([-gx, gy, np.ones_like(gx)], -1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    # Base colour: warm gold, raised parts slightly brighter (worn), recesses darker.
    gold = np.array([1.0, 0.76, 0.34], np.float32)
    shade = 0.78 + 0.22 * np.clip(height, 0, 1)
    colour = gold[None, None, :] * shade[..., None]
    # Right column (u > 0.75 of the image width is not used by the face disc corners): the rim strip uses the
    # bottom-right corner block, plain gold with fine knurling.
    rim = (x > size * 0.875) & (y > size * 0.875)
    knurl = 0.85 + 0.15 * (np.sin(x * 1.6) > 0)
    colour[rim] = gold * knurl[rim][:, None]
    normal[rim] = [0.0, 0.0, 1.0]
    os.makedirs(TEXTURES, exist_ok=True)
    save_png(colour, 'gold_coin_basecolor.png')
    save_png(normal * 0.5 + 0.5, 'gold_coin_normal.png')


def save_png(rgb, name):
    """rgb: rows top to bottom, values 0..1, written as an 8-bit PNG through Blender's image API (no Pillow)."""
    height, width = rgb.shape[:2]
    image = bpy.data.images.new(name, width, height, alpha=False)
    rgba = np.concatenate([rgb[::-1], np.ones((height, width, 1), np.float32)], -1)
    image.pixels[:] = np.clip(rgba, 0, 1).ravel()
    image.filepath_raw = os.path.join(TEXTURES, name)
    image.file_format = 'PNG'
    image.save()
    bpy.data.images.remove(image)


def add_coin(bm, uv_layer, colour_layer, matrix, brightness, closed=False):
    """One octagonal coin at matrix (local z up, radius 1): the top disc mapped onto the face disc of the texture,
    the rim onto the rim block; the bottom disc only when closed (a coin lying on the heap never shows it)."""
    ring = [(math.cos(2 * math.pi * k / SIDES), math.sin(2 * math.pi * k / SIDES)) for k in range(SIDES)]
    top = [bm.verts.new(matrix @ Vector((c, s, THICKNESS / 2))) for c, s in ring]
    bottom = [bm.verts.new(matrix @ Vector((c, s, -THICKNESS / 2))) for c, s in ring]
    faces = []

    def face(verts, uvs):
        created = bm.faces.new(verts)
        for loop, uv in zip(created.loops, uvs):
            loop[uv_layer].uv = uv
        faces.append(created)
    face(top, [(0.5 + 0.43 * c, 0.5 + 0.43 * s) for c, s in ring])
    if closed:
        face(bottom[::-1], [(0.5 + 0.43 * c, 0.5 - 0.43 * s) for c, s in ring][::-1])
    for k in range(SIDES):
        n = (k + 1) % SIDES
        face([bottom[k], bottom[n], top[n], top[k]], [(0.9, 0.02), (0.98, 0.02), (0.98, 0.1), (0.9, 0.1)])
    for created in faces:
        for loop in created.loops:
            loop[colour_layer] = (brightness, brightness, brightness, 1.0)


def mound_height(r, radius, peak):
    return peak * max(0.0, 1.0 - (r / radius) ** 2) ** 1.3


def build(icon, entry):
    rng = random.Random(icon)
    box = entry['opaque_box']
    width, height = box[2] - box[0], box[3] - box[1]
    # Coins across the heap from its painted width (a painted coin is about 22 x2 px wide); count from the area.
    radius = width / 2 / 11.0 * 1.0
    peak = radius * min(0.55, height / width * 0.95)
    count = int(14 + 2.0 * radius * radius)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    colour_layer = bm.loops.layers.color.new('Color')
    # The mound: a dome a little under the coins.
    rings, segments = 5, 16
    centre = bm.verts.new((0, 0, peak * 0.65))
    previous = None
    mound_faces = []
    for i in range(1, rings + 1):
        r = radius * 0.92 * i / rings
        z = mound_height(r, radius * 0.92, peak * 0.65)
        current = [bm.verts.new((r * math.cos(2 * math.pi * k / segments), r * math.sin(2 * math.pi * k / segments),
                                 z)) for k in range(segments)]
        for k in range(segments):
            n = (k + 1) % segments
            mound_faces.append(bm.faces.new([centre, current[k], current[n]]) if previous is None
                               else bm.faces.new([previous[k], current[k], current[n], previous[n]]))
        previous = current
    mound_faces.append(bm.faces.new(previous[::-1]))
    for created in mound_faces:
        for loop in created.loops:
            loop[uv_layer].uv = (0.94, 0.06)
            loop[colour_layer] = (0.45, 0.45, 0.45, 1.0)
    # Loose coins on the mound's surface, biased toward the middle, lying on its slope.
    for _ in range(count):
        r = radius * math.sqrt(rng.random()) * 1.02
        a = rng.random() * 2 * math.pi
        x, y = r * math.cos(a), r * math.sin(a)
        z = mound_height(r, radius * 0.92, peak * 0.65) + rng.uniform(0.0, 0.18)
        slope = 2 * 1.3 * peak * 0.65 * r / (radius * 0.92) ** 2 * max(0.0, 1 - (r / (radius * 0.92)) ** 2) ** 0.3
        up = Vector((x, y, 0)).normalized() * slope + Vector((0, 0, 1)) if r > 1e-3 else Vector((0, 0, 1))
        up.normalize()
        tilt = Vector((rng.gauss(0, 0.25), rng.gauss(0, 0.25), 1)).normalized()
        frame = up.to_track_quat('Z', 'Y') @ Vector((0, 0, 1)).rotation_difference(tilt)
        matrix = Matrix.Translation((x, y, z + THICKNESS / 2)) @ frame.to_matrix().to_4x4() \
            @ Matrix.Rotation(rng.random() * math.tau, 4, 'Z')
        brightness = min(1.0, 0.62 + 0.38 * (z / max(peak, 1e-3)) + rng.uniform(-0.06, 0.06))
        add_coin(bm, uv_layer, colour_layer, matrix, brightness)
    # Short stacks on larger heaps.
    stacks = 0 if radius < 5 else (1 if radius < 6.5 else 3)
    for s in range(stacks):
        a = rng.random() * 2 * math.pi
        r = radius * rng.uniform(0.25, 0.55)
        x, y = r * math.cos(a), r * math.sin(a)
        z = mound_height(r, radius * 0.92, peak * 0.65)
        for level in range(rng.randint(4, 8)):
            matrix = Matrix.Translation((x + rng.uniform(-0.05, 0.05), y + rng.uniform(-0.05, 0.05),
                                         z + THICKNESS * (level + 0.5) * 1.02)) \
                @ Matrix.Rotation(rng.random() * math.tau, 4, 'Z')
            add_coin(bm, uv_layer, colour_layer, matrix, 0.9 + rng.uniform(-0.05, 0.05), closed=level == 0)
    xs, ys, zs = ([v.co[i] for v in bm.verts] for i in range(3))
    shift = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    for v in bm.verts:
        v.co -= shift
    return bm


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = set(args)
    manifest = json.load(open(os.path.join(HERE, 'work', 'gold_manifest.json')))
    coin_textures()
    pl.TEXTURES = TEXTURES
    out_dir = os.path.join(HERE, 'work', 'gold')
    os.makedirs(out_dir, exist_ok=True)
    pl.WORK = out_dir
    for icon, entry in manifest.items():
        if only and icon not in only:
            continue
        pl.reset()
        bm = build(icon, entry)
        material = pl.material('gold_coin', 'gold_coin', roughness=0.38, metallic=0.7, normal=True)
        obj = pl.to_object(icon, bm, [material], 35)
        print('GOLD', icon, len(obj.data.polygons), 'triangles')
        pl.export(obj, icon)


main()
