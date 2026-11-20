"""Shared helpers for the 2026-10-30 mouth rebuild (Blender): parts, part roles, interior-face test."""
import bmesh, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

UPPER = {'Xheadpiv', 'Xhead', 'Xjawbase', 'Xtopfinpiv', 'Xtopfinpiv01', 'Xfinpiv', 'Xfinpiv01'}
LOWER = {'Xjaw', 'Xjawpivot', 'Xchinfinpiv', 'Xchinfinpiv01', 'Xbotfinpiv', 'Xbotfinpiv01', 'Xtong', 'Xtongpiv'}
MOUTH_BOX = ((-0.8, 0.8), (-5.3, -3.0), (14.55, 15.7))   # x, y, z (bind, rig space)


def parts(bm):
    bm.verts.ensure_lookup_table()
    comp = -np.ones(len(bm.verts), int); cid = 0
    for v in bm.verts:
        if comp[v.index] >= 0:
            continue
        st = [v]; comp[v.index] = cid
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if comp[y.index] < 0:
                    comp[y.index] = cid; st.append(y)
        cid += 1
    return comp


def in_box(p, box=MOUTH_BOX):
    return all(lo <= c <= hi for c, (lo, hi) in zip(p, box))


def roles(bm, comp):
    """{'shell': id, 'teeth': [ids], 'eyes': [ids], 'tongue': id or None}: small parts inside the mouth box."""
    CO = np.array([tuple(v.co) for v in bm.verts])
    n = np.bincount(comp)
    shell = int(n.argmax())
    out = {'shell': shell, 'teeth': [], 'eyes': [], 'tongue': None}
    for k in range(len(n)):
        if k == shell or n[k] > 80:
            continue
        P = CO[comp == k]; c = P.mean(0)
        if not in_box(c):
            continue
        if abs(c[0]) > 0.35 and c[2] > 15.2 and n[k] >= 20:
            out['eyes'].append(k)
        elif n[k] >= 40 and abs(c[0]) < 0.1 and np.ptp(P[:, 1]) > 0.6:
            out['tongue'] = k
        else:
            out['teeth'].append(k)
    return out


def interior_faces(bm, comp, shell, reach=1.6, cone_deg=30):
    """Main-shell faces inside the mouth box that cannot see out: rays along the normal and 6 directions on a cone
    around it all hit the main shell within `reach` (teeth, eyes and tongue are not occluders)."""
    verts = [tuple(v.co) for v in bm.verts]
    polys = [[v.index for v in f.verts] for f in bm.faces if comp[f.verts[0].index] == shell]
    bvh = BVHTree.FromPolygons(verts, polys, all_triangles=True)
    out = set()
    ca, sa = math.cos(math.radians(cone_deg)), math.sin(math.radians(cone_deg))
    for f in bm.faces:
        if comp[f.verts[0].index] != shell:
            continue
        c = f.calc_center_median()
        if not in_box(c):
            continue
        n = f.normal.normalized()
        t = n.orthogonal().normalized(); b = n.cross(t)
        dirs = [n] + [(n * ca + (t * math.cos(a) + b * math.sin(a)) * sa).normalized()
                      for a in np.linspace(0, 2 * math.pi, 7)[:-1]]
        if all(bvh.ray_cast(c + d * 1e-4, d, reach)[0] is not None for d in dirs):
            out.add(f.index)
    return out
