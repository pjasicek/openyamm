"""Thrown items traced from their side-view item sprites -> work/<name>_export.glb (engine/models/projectile_<name>.glb).
- dagger (object 307, thrown daggers: party and MM9 knives; 3dagger, 66 long): grip at the back, tip forward;
- axe (309, thrown axes; 3axe, 110 long): head forward;
- egg (384, MM9 egg; 3egg, 52 long).
Rings along the sprite's length follow its top and bottom outline per column (stations where the outline changes);
each ring is an ellipse with the sprite's height and a width of WIDTH(x) x that height (thin blades, round grips).
UVs project the side view onto textures/<name>_basecolor.png (make_solid_textures.py): the ring point at angle a takes
the row centre - half height x sin(a), so both faces show the painting and the edge rows wrap the sides. Pointed
ends close on a tip vertex. Flight along -Y; LENGTH is printed for engine/models/projectiles.yml.
Usage: blender --background --python build_traced.py -- <name> [...]"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import projlib as pl  # noqa: E402

# name: (sprite, sides, width ratio by sprite column, forward to the right?, max station step in px, outline change
#        that adds a station in px, roughness, metallic)
ITEMS = {
    'dagger': ('3dagger_p547.png', 4, lambda x: 1.0 if x < 40 else 0.8 if x < 54 else 0.3, True, 8, 1.5, 0.4, 0.0),
    'axe': ('3axe_p547.png', 6, lambda x: 0.14 if x < 40 else 0.8, False, 12, 1.5, 0.55, 0.0),
    'egg': ('3egg_p547.png', 8, lambda x: 1.0, True, 12, 7.0, 0.6, 0.0),
}
UNIT = 0.01        # Blender units per world unit; a sprite pixel at x2 is half a world unit


def outline(sprite):
    image = bpy.data.images.load(pl.sprite_path(sprite), check_existing=True)
    width, height = image.size
    alpha = np.array(image.pixels[:], np.float32).reshape(height, width, 4)[::-1, :, 3] >= 0.5
    columns = {}
    for x in range(width):
        rows = np.nonzero(alpha[:, x])[0]
        if len(rows):
            columns[x] = (float(rows.min()), float(rows.max()) + 1.0)
    return columns, width, height


def stations(columns, step, change):
    """Columns where the outline changes by more than a pixel since the last station, at most step apart."""
    xs = sorted(columns)
    chosen = [xs[0]]
    for x in xs[1:-1]:
        top, bottom = columns[x]
        last_top, last_bottom = columns[chosen[-1]]
        if x - chosen[-1] >= step or abs(top - last_top) > change or abs(bottom - last_bottom) > change:
            chosen.append(x)
    chosen.append(xs[-1])
    return chosen


def build(name):
    sprite, sides, width_ratio, forward_right, step, change, roughness, metallic = ITEMS[name]
    columns, width, height = outline(sprite)
    canvas = (1 << (width - 1).bit_length(), 1 << (height - 1).bit_length())
    xs = stations(columns, step, change)
    centre_x = 0.5 * (xs[0] + xs[-1] + 1)
    centre_row = 0.5 * height
    direction = -1.0 if forward_right else 1.0

    def position(x, side, up):
        return ((side) * UNIT * 0.5, direction * (x - centre_x) * UNIT * 0.5, up * UNIT * 0.5)

    def uv(x, row):
        return ((x + 0.5) / canvas[0], 1.0 - row / canvas[1])

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    rings = []
    for x in xs:
        top, bottom = columns[x]
        centre, half = 0.5 * (top + bottom), 0.5 * (bottom - top)
        half_width = half * width_ratio(x)
        ring = []
        for k in range(sides):
            angle = 2.0 * math.pi * (k + 0.5) / sides
            side, up = half_width * math.cos(angle), half * math.sin(angle)
            ring.append((position(x + 0.5, side, centre_row - centre + up), uv(x, centre - up)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(sides):
            n = (k + 1) % sides
            quad = [a[k], a[n], b[n], b[k]] if forward_right else [a[k], b[k], b[n], a[n]]
            pl.add_face(bm, uv_layer, quad)
    # End caps: a tip vertex half a pixel beyond each end ring, at its centre.
    for ring, x, outward in ((rings[0], xs[0] - 0.5, -1), (rings[-1], xs[-1] + 1.5, 1)):
        top, bottom = columns[min(max(int(x), xs[0]), xs[-1])]
        centre = 0.5 * (top + bottom)
        tip = (position(x, 0.0, centre_row - centre), uv(x, centre))
        for k in range(sides):
            n = (k + 1) % sides
            # The front cap (the -Y end) winds k -> n seen from the tip, the back cap the other way.
            tri = [tip, ring[k], ring[n]] if (outward > 0) == forward_right else [tip, ring[n], ring[k]]
            pl.add_face(bm, uv_layer, tri)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    obj = pl.to_object(name.capitalize(), bm, [pl.material(name.capitalize(), name, roughness, metallic)], 50)
    ys = [v.co.y for v in obj.data.vertices]
    print('LENGTH', name, round((max(ys) - min(ys)) / UNIT, 1))
    pl.export(obj, name)


def main():
    for name in sys.argv[sys.argv.index('--') + 1:]:
        pl.reset()
        build(name)


main()
