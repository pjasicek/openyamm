"""Weld the grafted head's neck rim to the body's neck rim (user review 2026-10-30: "the graft has a clear line on the
neck"; overlapping shells showed the outer rim's ragged edge and a shading step). graft_head_parts.py with "weld"
leaves both rims on the same cut plane, the body's neck tapered onto the head's ring. Here, on the joined body:
- the rims are the boundary vertices of the head piece and of the neck piece within 1.5 mm of the cut plane
  (work/graft.json z_cut; no loop order: the female's rim touches itself beside the braid);
- every body rim vertex is projected onto the nearest head rim edge and splits it there (unless it lands within
  0.3 mm of a head vertex; nothing within 6 mm: left alone), then every unmatched head rim vertex splits the body
  rim the same way; each body rim vertex is moved onto its partner and welded to it, so the seam shares its
  vertices (one smooth normal across it);
- faces that gained a vertex are triangulated. The welded vertices keep the head's piece id; export_uploads_graft.py
  reads the face attribute 'head' written here before the weld (welded vertices cannot tell).
Used by prepare_rig.py (pf4) and step1_clean.py (pm3) right after the parts are joined. weld(body, head, neck)"""
import bmesh, json, os
import numpy as np
from mathutils import Vector
from mathutils.geometry import intersect_point_line


def nearest_edge(edges, p):
    best = None
    for e in edges:
        a, b = e.verts[0].co, e.verts[1].co
        _, t = intersect_point_line(p, a, b)
        t = min(max(t, 0.0), 1.0); q = a.lerp(b, t); d = (q - p).length
        if best is None or d < best[0]:
            best = (d, e, t, q)
    return best


def split_at(bm, edges, verts, p, tol=3e-4, reach=0.006):
    """The rim vertex at p: an existing one within tol, else a new one splitting the nearest rim edge (None when no
    rim edge is within reach: a stretch of the other rim hidden under the braid)."""
    found = nearest_edge(edges, p)
    if found is None or found[0] > reach:
        return None
    d, e, t, q = found
    for v in e.verts:
        if (v.co - q).length < tol:
            return v
    a = e.verts[0]
    edges.discard(e)
    ne, nv = bmesh.utils.edge_split(e, a, t)
    edges.update(x for x in nv.link_edges if x.is_boundary)
    verts.add(nv)
    return nv


def weld(body, head_piece, neck_piece, z_cut, plane_tol=0.0015):
    me = body.data
    bm = bmesh.new(); bm.from_mesh(me)
    pl = bm.verts.layers.int['piece']
    hl = bm.faces.layers.int.get('head') or bm.faces.layers.int.new('head')   # head faces, fixed before the weld
    for f in bm.faces:
        f[hl] = int(all(v[pl] == head_piece for v in f.verts))
    on = lambda v, piece: v[pl] == piece and abs(v.co.z - z_cut) < plane_tol
    Hv = {v for e in bm.edges if e.is_boundary for v in e.verts if on(v, head_piece)}
    Bv = {v for e in bm.edges if e.is_boundary for v in e.verts if on(v, neck_piece)}
    He = {e for e in bm.edges if e.is_boundary and all(v in Hv for v in e.verts)}
    Be = {e for e in bm.edges if e.is_boundary and all(v in Bv for v in e.verts)}
    gaps = [nearest_edge(He, v.co)[0] for v in Bv]
    pairs = {}
    for b in list(Bv):
        h = split_at(bm, He, Hv, b.co.copy())
        if h is not None:
            pairs[b] = h
    taken = set(pairs.values())
    for h in list(Hv):
        if h in taken:
            continue
        b = split_at(bm, Be, Bv, h.co.copy())
        if b is not None and b not in pairs:
            pairs[b] = h
    for b, h in pairs.items():
        b.co = h.co.copy()
    touched = {f for v in list(pairs) + list(pairs.values()) for f in v.link_faces}
    bmesh.ops.weld_verts(bm, targetmap=pairs)
    big = [f for f in bm.faces if f in touched and f.is_valid and len(f.verts) > 4]
    bmesh.ops.triangulate(bm, faces=big)
    left = sum(1 for e in bm.edges if e.is_boundary and all(abs(v.co.z - z_cut) < plane_tol for v in e.verts))
    bm.to_mesh(me); bm.free(); me.update()
    print('WELD neck: head rim', len(Hv), 'verts, body rim', len(Bv), 'verts, gap before mm p50 %.2f p90 %.2f max %.2f'
          % tuple(np.percentile(np.array(gaps) * 1000, [50, 90, 100])), 'welded', len(pairs), 'faces triangulated',
          len(big), 'open rim edges left', left)


def mark_head_faces(body, head_piece):
    me = body.data
    pc = [0] * len(me.vertices); me.attributes['piece'].data.foreach_get('value', pc)
    a = me.attributes.get('head') or me.attributes.new('head', 'INT', 'FACE')
    a.data.foreach_set('value', [int(all(pc[v] == head_piece for v in p.vertices)) for p in me.polygons])


def weld_from_graft(body, work_dir):
    g = json.load(open(os.path.join(work_dir, 'graft.json')))
    if g.get('weld', True):
        weld(body, g['head'], g['neck_piece'], g['z_cut'])
    else:                                              # pm3: the joint is hidden inside the tunic, nothing to weld
        mark_head_faces(body, g['head'])
        print('WELD skipped (graft without weld): head faces marked')
