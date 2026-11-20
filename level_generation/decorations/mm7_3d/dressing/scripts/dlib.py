"""Shared helpers of the MM7 dressing batch: the MM6 hanging batch's builders (../../../mm6_dungeons_3d/hanging/
scripts/hanging_lib.py, read only: swept tubes, chain links, rings, rivets, COLOR_0 tint toward native colours)
and the New Sorpigal props library (pl: lathe, tube, box, join, occlusion, export, renders), with materials found in
this batch's textures/ first. Sizes are in map units (81.7 per metre) unless a name says metres."""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
DECO = os.path.join(REPO, 'level_generation', 'decorations')
sys.path.insert(0, os.path.join(DECO, 'mm6_dungeons_3d', 'hanging', 'scripts'))
import hanging_lib as hl  # noqa: E402

dl = hl.dl
pl = hl.pl
u = hl.u
UNITS_PER_METRE = dl.UNITS_PER_METRE
TEXTURES = os.path.join(HERE, 'textures')
WORK = os.path.join(HERE, 'work')
REVIEW = os.path.join(HERE, 'review')
X2 = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
NATIVE_BMP = os.path.join(REPO, 'assets_dev', '_legacy', 'sprites_original')
MM6_BONES = os.path.join(DECO, 'mm6_dungeons_3d', 'bones')
MM6_HANGING = os.path.join(DECO, 'mm6_dungeons_3d', 'hanging')
MODELS_MM6 = os.path.join(REPO, 'assets_source', 'worlds', 'mm6', 'models')
MODELS_ENGINE = os.path.join(REPO, 'assets_source', 'engine', 'models')


def material(name, texture, alpha=False, extras=None):
    """Material from textures/<texture>_{basecolor,normal,mr}.png here, else the MM6 hanging/dungeon/props textures."""
    if os.path.exists(os.path.join(TEXTURES, f'{texture}_basecolor.png')):
        saved = pl.TEX
        pl.TEX = TEXTURES
        try:
            return pl.material(name, texture, alpha=alpha, extras=extras)
        finally:
            pl.TEX = saved
    return hl.material(name, texture, alpha=alpha, extras=extras)


def apply(obj):
    return hl.apply(obj)


def fix_winding(obj):
    """Turn every closed loose part of obj outward (positive signed volume): the engine culls the back faces of
    single-sided materials, so an inside-out part disappears in game while Blender's renders still show it.
    Parts are split by shared positions, as tools' check_winding.py does. Returns the number of parts flipped."""
    import bmesh
    from mathutils import Vector
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    key = {v: tuple(round(c, 6) for c in v.co) for v in bm.verts}
    by_pos = {}
    for f in bm.faces:
        for v in f.verts:
            by_pos.setdefault(key[v], []).append(f.index)
    parent = list(range(len(bm.faces)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for faces in by_pos.values():
        for f in faces[1:]:
            a, b = find(faces[0]), find(f)
            if a != b:
                parent[a] = b
    groups = {}
    for f in bm.faces:
        groups.setdefault(find(f.index), []).append(f)
    flipped = 0
    for faces in groups.values():
        edges = {}
        volume = 0.0
        for f in faces:
            pts = [Vector(key[v]) for v in f.verts]
            for i in range(1, len(pts) - 1):
                volume += pts[0].dot(pts[i].cross(pts[i + 1])) / 6.0
            for i in range(len(pts)):
                e = tuple(sorted((key[f.verts[i]], key[f.verts[(i + 1) % len(pts)]])))
                edges[e] = edges.get(e, 0) + 1
        closed = all(n == 2 for n in edges.values())
        if closed and volume < 0:
            bmesh.ops.reverse_faces(bm, faces=faces)
            flipped += 1
    bm.to_mesh(obj.data); bm.free()
    obj.data.update()
    return flipped


def save(prop, lods):
    """Turn closed parts outward (fix_winding), save work/<prop>.blend (review.py renders it) and export
    work/<prop>_export.glb (finish.py links the LODs).
    lods: [LOD0, LOD1, ...] named Base, Base_LOD1, ..."""
    os.makedirs(WORK, exist_ok=True)
    print('WINDING fixed', prop, [fix_winding(o) for o in lods])
    lo, hi = pl.bounds(lods[:1])
    print('BOUNDS', prop, [round(v * UNITS_PER_METRE, 1) for v in lo], [round(v * UNITS_PER_METRE, 1) for v in hi])
    print('TRIS', prop, [pl.triangles(o) for o in lods])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{prop}.blend'))
    pl.export(lods, os.path.join(WORK, f'{prop}_export.glb'))
