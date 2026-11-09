"""Books: every icon of the books manifest -> work/books/<icon>_export.glb, a closed book lying on its back cover.

The icons paint each book at an angle, so projecting them made skewed boxes. The book is built instead: two cover
boards overhanging a page block on three sides, a rounded spine joining the boards, cream page edges with fine page
lines. Its texture is an atlas (textures/<icon>_book.png, 1024 x 1024) of flat, straight-on paintings from Codex
(books_hd/<icon>_cover.png and <icon>_spine.png, from the icon; books_hd/CODEX_BRIEF_*.md): the cover in the left
two thirds, the spine next to it and procedural page edges at the right. Board edges sample the cover's border. The
back cover reuses the front painting, darkened (it lies on the ground). Height along +Y, the spine at -X, lowest point
at 0, footprint centred; the binding's length (the books' common length) sets the world size.
Usage: blender --background --python build_books.py -- [icon ...]"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'projectiles_claude',
                                'scripts'))
import projlib as pl  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTURES = os.path.join(HERE, 'textures')
SOURCES = os.path.join(HERE, 'books_hd')
ATLAS = 1024
# Atlas columns (u): cover, spine, page edges.
COVER_U, SPINE_U, PAGES_U = (0.0, 0.66), (0.67, 0.8), (0.81, 1.0)
WIDTH, HEIGHT, THICKNESS = 0.72, 1.0, 0.27       # the book, in Blender units (height 1)
BOARD, OVERHANG, SPINE_SEGMENTS = 0.028, 0.025, 8


def load_rgb(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    rgb = np.array(image.pixels[:], np.float32).reshape(height, width, image.channels)[::-1, :, :3]
    bpy.data.images.remove(image)
    return rgb


def resize(rgb, width, height):
    """Box-filtered resize (numpy only): sample the source at the centre of each target pixel's footprint."""
    source_h, source_w = rgb.shape[:2]
    ys = ((np.arange(height) + 0.5) * source_h / height).astype(int).clip(0, source_h - 1)
    xs = ((np.arange(width) + 0.5) * source_w / width).astype(int).clip(0, source_w - 1)
    return rgb[ys][:, xs]


def atlas_for(icon):
    cover_path = os.path.join(SOURCES, f'{icon}_cover.png')
    spine_path = os.path.join(SOURCES, f'{icon}_spine.png')
    if not os.path.exists(cover_path):
        raise FileNotFoundError(cover_path)
    atlas = np.zeros((ATLAS, ATLAS, 3), np.float32)
    columns = [int(u * ATLAS) for u in (*COVER_U, *SPINE_U, *PAGES_U)]
    cover = load_rgb(cover_path)
    atlas[:, columns[0]:columns[1]] = resize(cover, columns[1] - columns[0], ATLAS)
    if os.path.exists(spine_path):
        atlas[:, columns[2]:columns[3]] = resize(load_rgb(spine_path), columns[3] - columns[2], ATLAS)
    else:
        strip = cover[:, :max(8, cover.shape[1] // 12)] * 0.8
        atlas[:, columns[2]:columns[3]] = resize(strip, columns[3] - columns[2], ATLAS)
    # Page edges: cream, the page lines running along the edge (u runs across the page stack, from board to board),
    # darker toward the boards, with slow unevenness along the edge.
    width = columns[5] - columns[4]
    pixels = np.arange(width, dtype=np.float32)[None, :]
    across = pixels / (width - 1)
    rows = np.arange(ATLAS, dtype=np.float32)[:, None]
    lines = 0.84 + 0.16 * (np.sin(pixels * 1.3 + np.sin(rows * 0.01) * 2.0) > 0.2)
    cream = np.array([0.86, 0.78, 0.6], np.float32)
    edge_shade = 0.62 + 0.38 * np.sin(across * math.pi) ** 0.5
    atlas[:, columns[4]:columns[5]] = cream[None, None, :] * (lines * edge_shade)[..., None]
    # The gaps between columns take their left neighbour's last column (mip bleed).
    for start, end in ((columns[1], columns[2]), (columns[3], columns[4])):
        atlas[:, start:end] = atlas[:, start - 1:start]
    save_png(atlas, f'{icon}_book_basecolor.png')


def save_png(rgb, name):
    height, width = rgb.shape[:2]
    image = bpy.data.images.new(name, width, height, alpha=False)
    rgba = np.concatenate([rgb[::-1], np.ones((height, width, 1), np.float32)], -1)
    image.pixels[:] = np.clip(rgba, 0, 1).ravel()
    image.filepath_raw = os.path.join(TEXTURES, name)
    image.file_format = 'PNG'
    image.save()
    bpy.data.images.remove(image)


def u_in(column, t):
    return column[0] + (column[1] - column[0]) * t


def build():
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    colour = bm.loops.layers.color.new('Color')

    def quad(corners, uvs, shade=1.0):
        face = bm.faces.new([bm.verts.new(c) for c in corners])
        for loop, texcoord in zip(face.loops, uvs):
            loop[uv].uv = texcoord
            loop[colour] = (shade, shade, shade, 1.0)
        return face

    def box(x0, x1, y0, y1, z0, z1, top_uv, outer_top, shade_outer):
        """A closed board: its outer face (the top when outer_top, else the bottom) mapped onto top_uv (u0, u1, v0,
        v1); the inner face (the endpaper side, seen past the page block) and the sides onto the cover's border."""
        border = (u_in(COVER_U, 0.004), u_in(COVER_U, 0.012))
        plain = [(border[0], 0.2), (border[1], 0.2), (border[1], 0.8), (border[0], 0.8)]
        quad([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
             [(top_uv[0], top_uv[2]), (top_uv[1], top_uv[2]), (top_uv[1], top_uv[3]), (top_uv[0], top_uv[3])]
             if outer_top else plain, shade_outer if outer_top else 0.55)
        quad([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
             [(top_uv[0], top_uv[3]), (top_uv[1], top_uv[3]), (top_uv[1], top_uv[2]), (top_uv[0], top_uv[2])]
             if not outer_top else plain, shade_outer if not outer_top else 0.55)
        side = [(border[0], 0.45), (border[1], 0.45), (border[1], 0.55), (border[0], 0.55)]
        quad([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], side, 0.8)
        quad([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], side, 0.8)
        quad([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], side, 0.8)
        quad([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], side, 0.8)

    cover_uv = (COVER_U[0], COVER_U[1], 0.0, 1.0)
    # Boards: back (on the ground) and front, spine side at x = 0.
    box(0.0, WIDTH, 0.0, HEIGHT, 0.0, BOARD, cover_uv, False, 0.6)
    box(0.0, WIDTH, 0.0, HEIGHT, THICKNESS - BOARD, THICKNESS, cover_uv, True, 1.0)
    # Page block, inset by the overhang on the top, bottom and fore-edge.
    x0, x1 = 0.02, WIDTH - OVERHANG
    y0, y1 = OVERHANG, HEIGHT - OVERHANG
    z0, z1 = BOARD, THICKNESS - BOARD
    pages = lambda a, b: (u_in(PAGES_U, a), u_in(PAGES_U, b))  # noqa: E731
    pu = pages(0.05, 0.95)
    quad([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
         [(pu[0], 0.02), (pu[0], 0.98), (pu[1], 0.98), (pu[1], 0.02)])            # fore-edge
    quad([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
         [(pu[0], 0.1), (pu[0], 0.7), (pu[1], 0.7), (pu[1], 0.1)], 0.85)          # bottom edge
    quad([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
         [(pu[0], 0.3), (pu[0], 0.9), (pu[1], 0.9), (pu[1], 0.3)], 0.9)           # top edge
    # Rounded spine: a half cylinder from the back board's outer edge to the front board's, bulging to -X.
    radius = THICKNESS / 2
    previous = None
    for i in range(SPINE_SEGMENTS + 1):
        # From the bottom (z 0) round to the top, bulging out by 0.45 of the radius.
        x = -radius * 0.45 * math.sin(math.pi * i / SPINE_SEGMENTS)
        z = radius - radius * math.cos(math.pi * i / SPINE_SEGMENTS)
        u = u_in(SPINE_U, i / SPINE_SEGMENTS)
        current = (bm.verts.new((x, -0.002, z)), bm.verts.new((x, HEIGHT + 0.002, z)), u)
        if previous is not None:
            face = bm.faces.new([previous[0], current[0], current[1], previous[1]])
            for loop, texcoord in zip(face.loops, [(previous[2], 0.0), (current[2], 0.0), (current[2], 1.0),
                                                     (previous[2], 1.0)]):
                loop[uv].uv = texcoord
                loop[colour] = (0.95, 0.95, 0.95, 1.0)
        previous = current
    for face in bm.faces:
        face.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    xs, ys, zs = ([v.co[i] for v in bm.verts] for i in range(3))
    centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs))
    for v in bm.verts:
        v.co.x -= centre[0]
        v.co.y -= centre[1]
        v.co.z -= centre[2]
    return bm


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = set(args)
    manifest = json.load(open(os.path.join(HERE, 'work', 'books_manifest.json')))
    pl.TEXTURES = TEXTURES
    out_dir = os.path.join(HERE, 'work', 'books')
    os.makedirs(out_dir, exist_ok=True)
    pl.WORK = out_dir
    for icon in manifest:
        if only and icon not in only:
            continue
        if not os.path.exists(os.path.join(SOURCES, f'{icon}_cover.png')):
            print('BOOK', icon, 'no cover yet')
            continue
        pl.reset()
        atlas_for(icon)
        material = pl.material(icon, f'{icon}_book', roughness=0.7)
        obj = pl.to_object(icon, build(), [material], 40)
        print('BOOK', icon, len(obj.data.polygons), 'triangles')
        pl.export(obj, icon)


main()
