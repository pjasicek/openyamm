"""Deterministic triangulation shared by the texture quality pass scripts (uv_texpass.py, head_uv_texpass.py,
transfer_texpass_uv.py), so a rebuilt body gets exactly the faces the new UV layouts were made on."""
import bmesh
from mathutils import Vector
from mathutils.kdtree import KDTree


def mirror_triangulate(me):
    """Triangulate non-head n-gons; -x faces follow the mirror image of their +x twin's diagonal."""
    bm = bmesh.new()
    bm.from_mesh(me)
    head = bm.faces.layers.int['head']
    ngons = [f for f in bm.faces if not f[head] and len(f.verts) != 3]
    plus = [f for f in ngons if f.calc_center_median().x > 0]
    minus = [f for f in ngons if f.calc_center_median().x < 0]
    assert len(plus) + len(minus) == len(ngons)
    tree = KDTree(len(plus))
    for i, f in enumerate(plus):
        c = f.calc_center_median()
        tree.insert((-c.x, c.y, c.z), i)
    tree.balance()
    twins = []
    for f in minus:
        _, i, d = tree.find(f.calc_center_median())
        if d > 1e-5:
            raise ValueError(f'no mirror twin for a -x n-gon ({d})')
        twins.append(i)
    shared = [0]
    pieces = []          # per +x n-gon: its triangles as lists of vertex positions
    for f in plus:
        res = bmesh.ops.triangulate(bm, faces=[f], quad_method='FIXED', ngon_method='EAR_CLIP')
        pieces.append([[v.co.copy() for v in t.verts] for t in res['faces']])
    for f, i in zip(minus, twins):
        verts = list(f.verts)
        tris = []
        for tri in pieces[i]:
            ms = [Vector((-c.x, c.y, c.z)) for c in tri]
            tris.append([min(verts, key=lambda v: (v.co - m).length) for m in ms][::-1])
        for t in tris:
            if bm.faces.get(t) is None:       # a sliver lying in the plane is shared with the +x twin
                bm.faces.new(t, f)
            else:
                shared[0] += 1
        bm.faces.remove(f)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    return {'ngons': len(ngons), 'shared_plane_triangles': shared[0]}


def triangulate_head(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    head = bm.faces.layers.int['head']
    ngons = [f for f in bm.faces if f[head] and len(f.verts) != 3]
    bmesh.ops.triangulate(bm, faces=ngons, quad_method='FIXED', ngon_method='EAR_CLIP')
    bm.to_mesh(me)
    bm.free()
    return len(ngons)
