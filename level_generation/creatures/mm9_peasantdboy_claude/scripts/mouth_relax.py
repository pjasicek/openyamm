"""Relax the pursed Meshy mouth (third pass, orchestrator: "a small pinched pucker/pout ... a duck pout in 3/4"). The
mirrored Meshy face has narrow lips pushed 3-4 mm forward of the face around a 2 cm slit. Head-shell vertices in an
ellipse around the mouth (half widths RX 2.8 cm, RZ 1.7 cm about the lip line; front only) get Laplacian steps on their
DEPTH (Blender y) only, weighted by a smooth falloff, so the lips settle onto the face's own curve; then a gentle smile:
vertices near the lip line beyond 0.9 cm from the midline move up by up to 1.2 mm towards the corners. The mouth slit's
rim moves with its neighbours (the export caps it). Positions only: UVs, weights and paints stay valid; the paint moves
with the surface. Symmetric again from the +x side. Args: <in blend> <out blend> [iters 14]"""
import bpy, bmesh, sys, math
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
IT = int(a[2]) if len(a) > 2 else 14
import os
CX, CZ, RX, RZ = 0.0, float(os.environ.get("CZ", 0.6935)), float(os.environ.get("RX", 0.028)), float(os.environ.get("RZ", 0.017))  # dboy: CZ 0.327 RX 0.024 RZ 0.014
bpy.ops.wm.open_mainfile(filepath=IN)
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
hl = bm.faces.layers.int['head']
hn = bm.faces.layers.int.get('hand')
headv = {v for f in bm.faces if f[hl] and not (hn and f[hn]) for v in f.verts}
# the face shell (largest connected head part)
comp = {}; big = None; best = 0
for v in headv:
    if v in comp:
        continue
    st = [v]; comp[v] = v; n = 0
    while st:
        x = st.pop(); n += 1
        for e in x.link_edges:
            y = e.other_vert(x)
            if y in headv and y not in comp:
                comp[y] = v; st.append(y)
    if n > best:
        best, big = n, v
shell = {v for v in headv if comp[v] is big}


def w(p):
    if p.y > -0.035:
        return 0.0
    r = math.sqrt((p.x / RX) ** 2 + ((p.z - CZ) / RZ) ** 2)
    return 0.0 if r >= 1 else 0.5 * (1 + math.cos(math.pi * r))


W = {v: w(v.co) for v in shell}
W = {v: x for v, x in W.items() if x > 1e-3}
y0 = {v: v.co.y for v in W}
for _ in range(IT):
    new = {}
    for v, x in W.items():
        nb = [e.other_vert(v) for e in v.link_edges if e.other_vert(v) in shell]
        if len(nb) < 2:
            continue
        avg = sum(n.co.y for n in nb) / len(nb)
        new[v] = v.co.y + (avg - v.co.y) * 0.6 * x
    for v, y in new.items():
        # only ever back (pout removed), never forward
        v.co.y = max(y, y0[v])
# gentle smile: corners up
for v, x in W.items():
    p = v.co
    ax = abs(p.x)
    if 0.009 < ax < RX and abs(p.z - CZ) < 0.008:
        lift = 0.0012 * min(1.0, (ax - 0.009) / 0.011) * max(0.0, 1 - abs(p.z - CZ) / 0.008) * min(1.0, (RX - ax) / 0.006)
        p.z += lift
# symmetric from +x
pos = [v for v in W if v.co.x > 1e-6]
kd = KDTree(len(pos))
for k, v in enumerate(pos):
    kd.insert(Vector((v.co.x, v.co.y, v.co.z)), k)
kd.balance()
for v in W:
    if v.co.x < -1e-6:
        q, k, d = kd.find(Vector((-v.co.x, v.co.y, v.co.z)))
        if d < 0.003:
            v.co = Vector((-q.x, q.y, q.z))
    elif abs(v.co.x) <= 1e-6:
        v.co.x = 0.0
# the small loose pieces inside the mouth (Meshy's slit plate, inner lips) follow the lips back: each vertex moves by the
# displacement of the nearest relaxed shell vertex, plus 0.5 mm so it stays behind the lips
inner = [v for v in headv if comp[v] is not big and v.co.y < -0.03 and
         math.sqrt((v.co.x / RX) ** 2 + ((v.co.z - CZ) / RZ) ** 2) < 1]
kd2 = KDTree(len(W)); WL = list(W)
for k, v in enumerate(WL):
    kd2.insert(Vector((v.co.x, y0[v], v.co.z)), k)
kd2.balance()
for v in inner:
    q, k, d = kd2.find(v.co)
    u = WL[k]
    v.co.y += (u.co.y - y0[u]) + (0.0005 if u.co.y - y0[u] > 1e-5 else 0.0)
moved = sum(1 for v in W if abs(v.co.y - y0[v]) > 1e-5)
mx = max(v.co.y - y0[v] for v in W)
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('MOUTHRELAX', {'verts': len(W), 'inner': len(inner), 'moved': moved, 'max_back_mm': round(mx * 1000, 2)})
