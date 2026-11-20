"""Front panel weights from the skin under it (user, round 3: the thigh skin came through the panel in Walking).
The installed panel splits every vertex evenly between both thighs (0.2 each on average, 0.41 each at the tip), so a
thigh swinging forward pushed through that side of the panel. Each panel vertex of REA_CAND takes the weights of the
nearest point (interpolated in the triangle) on the body skin behind it, top 4 influences, so the leotard deforms with
the legs and keeps its 8 mm offset. In: work/<REA_LADDER, ladder_head.blend>; out: work/ladder_head_panel.blend."""
import os, bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_LADDER', 'ladder_head.blend')))
cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_66')]; me = cand.data


def islands(me):
    adj = [[] for _ in me.vertices]
    for e in me.edges:
        a, b = e.vertices; adj[a].append(b); adj[b].append(a)
    lab = [-1] * len(me.vertices); n = 0
    for s in range(len(me.vertices)):
        if lab[s] < 0:
            st = [s]; lab[s] = n
            while st:
                for w in adj[st.pop()]:
                    if lab[w] < 0:
                        lab[w] = n; st.append(w)
            n += 1
    return lab


def panel_and_body(me):
    """Panel: the island of 100-200 vertices centred on x = 0 in front of the hips; skin: the other islands of more than 150
    vertices (torso, and the separate leg shell, 188 vertices in the 66 % mesh)."""
    lab = islands(me); groups = {}
    for v in me.vertices:
        groups.setdefault(lab[v.index], []).append(v)
    body = {k for k, vs in groups.items() if len(vs) > 150}
    def centre(vs):
        return [sum(v.co[i] for v in vs) / len(vs) for i in range(3)]
    panel = [k for k, vs in groups.items() if 100 <= len(vs) <= 200 and abs(centre(vs)[0]) < 0.03
             and centre(vs)[1] < -0.12 and min(v.co.z for v in vs) < 0.75]
    assert len(panel) == 1, panel
    return lab, panel[0], body - {panel[0]}


lab, panel, body = panel_and_body(me)
pv = [v.index for v in me.vertices if lab[v.index] == panel]
gname = {g.index: g.name for g in cand.vertex_groups}
cloak = {i for i, n in gname.items() if n.startswith('Cloak')}
nocloak = [not any(g.group in cloak and g.weight > 0 for g in v.groups) for v in me.vertices]
bf = [p for p in me.polygons if lab[p.vertices[0]] in body and all(nocloak[i] for i in p.vertices)]
tree = BVHTree.FromPolygons([v.co[:] for v in me.vertices], [tuple(p.vertices) for p in bf])


def weights(i):
    return {gname[g.group]: g.weight for g in me.vertices[i].groups if gname[g.group] != 'ReduceProtect'}


new = {}; far = 0
for i in pv:
    co = me.vertices[i].co; loc, nrm, fi, d = tree.ray_cast(co, Vector((0, 1, 0)), 0.06)  # the skin behind it
    if loc is None:
        loc, nrm, fi, d = tree.find_nearest(co); far += 1
    tri = bf[fi].vertices; acc = {}
    if len(tri) != 3:
        raise SystemExit('triangles expected')
    a, b, c = (me.vertices[t].co for t in tri); v0, v1, v2 = b - a, c - a, loc - a
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01; l1 = (d11 * d20 - d01 * d21) / den; l2 = (d00 * d21 - d01 * d20) / den
    bary = [max(0.0, 1 - l1 - l2), max(0.0, l1), max(0.0, l2)]
    for t, l in zip(tri, bary):
        for name, w in weights(t).items():
            acc[name] = acc.get(name, 0.0) + w * l
    top = sorted(acc.items(), key=lambda x: -x[1])[:4]; s = sum(w for _, w in top)
    new[i] = [(n, w / s) for n, w in top]
# the centre keeps the installed even split (skin weights there switch from one thigh to the other at x = 0 and the
# tip between the legs crumpled); the skin weights take over toward the sides, then a few smoothing passes
X0, X1, PASSES = (float(os.environ.get(k, d)) for k, d in (('PANEL_X0', '0.015'), ('PANEL_X1', '0.07'), ('PANEL_SMOOTH', '4')))
for i in pv:
    t = min(1.0, max(0.0, (abs(me.vertices[i].co.x) - X0) / (X1 - X0))); t = t * t * (3 - 2 * t)
    acc = {n: (1 - t) * w for n, w in weights(i).items()}
    for n, w in new[i]:
        acc[n] = acc.get(n, 0.0) + t * w
    new[i] = acc
nb = {i: set() for i in pv}
for e in me.edges:
    a, b = e.vertices
    if a in nb and b in nb:
        nb[a].add(b); nb[b].add(a)
for _ in range(int(PASSES)):
    nxt = {}
    for i in pv:
        acc = {n: 0.5 * w for n, w in new[i].items()}
        for j in nb[i]:
            for n, w in new[j].items():
                acc[n] = acc.get(n, 0.0) + 0.5 * w / len(nb[i])
        nxt[i] = acc
    new = nxt
for i in pv:
    top = sorted(new[i].items(), key=lambda x: -x[1])[:4]; s = sum(w for _, w in top)
    new[i] = [(n, w / s) for n, w in top]
for i, ws in new.items():
    for g in list(me.vertices[i].groups):
        cand.vertex_groups[g.group].remove([i])
    for name, w in ws:
        cand.vertex_groups[name].add([i], w, 'REPLACE')
tot = {}
for ws in new.values():
    for n, w in ws:
        tot[n] = tot.get(n, 0.0) + w / len(new)
print('PANEL', len(pv), 'vertices,', far, 'by nearest point, mean weights', {k: round(v, 3) for k, v in sorted(tot.items(), key=lambda x: -x[1])[:6]})
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_head_panel.blend'))
