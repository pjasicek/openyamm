"""(Finding, 2026-11-02: the face shell is CLOSED at the mouth; the two open "slits" were the rims of Meshy's loose lip
pieces (two 18-vertex pieces and a 24-vertex plate) floating in front of it: the pale lumpy lower-lip bulge and the
specks. Deleting them (step 1) leaves one smooth closed surface; steps 2 find no loop and do nothing.)
One closed mouth (fourth pass, user: "look at his mouth": a painted line above a pale lumpy lower-lip bulge, tooth specks
in the slit). Positions/faces only, after mouth_relax.py:
1. the small loose pieces inside the mouth (Meshy's slit plate and inner lips: head parts under 40 vertices within the
   mouth ellipse) are deleted;
2. the slit (the head-shell boundary loop nearest the mouth) is closed: every rim vertex moves onto one lip line (the
   loop's mean height at the centre, the corners up by the loop's own corner rise) and the loop's mean depth there, and
   upper/lower rim vertices at the same x are welded, so the lips meet in one seam with nothing behind it;
3. the lips' depth is relaxed again (`mouth_relax.py`'s weights, ITERS steps, never forward) so the lower-lip bulge settles.
Writes the closed lip line as work/mouth_line.json (x, glTF y = z + LIFT) for face_paint_fix.py. Args: <in> <out> [iters 10]"""
import bpy, bmesh, sys, math, json
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
IT = int(a[2]) if len(a) > 2 else 10
LIFT = 0.4825
CZ, RX, RZ = 0.6935, 0.028, 0.017
bpy.ops.wm.open_mainfile(filepath=IN)
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
hl = bm.faces.layers.int['head']
hn = bm.faces.layers.int.get('hand')
headv = {v for f in bm.faces if f[hl] and not (hn and f[hn]) for v in f.verts}
comp = {}; sizes = {}
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
    sizes[v] = n
big = max(sizes, key=sizes.get)
inmouth = lambda p: p.y < -0.03 and math.sqrt((p.x / RX) ** 2 + ((p.z - CZ) / RZ) ** 2) < 1
drop = {v for v in headv if comp[v] is not big and sizes[comp[v]] < 40 and inmouth(v.co)}
bmesh.ops.delete(bm, geom=list(drop), context='VERTS')
bm.verts.ensure_lookup_table()
# slit loop (shell faces only)
shellv = {v for v in bm.verts if v in comp and comp[v] is big}
shellf = {f for f in bm.faces if all(v in shellv for v in f.verts)}
bnd = {e for e in bm.edges if e.is_boundary and e.link_faces and e.link_faces[0][hl]}
loops = []
while bnd:
    e = bnd.pop(); lp = [e]; st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for f in v.link_edges:
                if f in bnd:
                    bnd.discard(f); lp.append(f); st.append(f)
    loops.append(lp)
# the mouth has TWO open loops on the shell: A between the lips (rest z 0.693-0.700) and B, a crease opening under the lower
# lip (z 0.683-0.692); the old export capped only B, so A stayed open over the inner pieces (the specks). Both close here.
# (the two traced as one 36-edge set here: split by edge height, A above rest z 0.692)
mouthedges = [e for lp in loops for e in lp if all(inmouth(v.co) for v in e.verts) and e.link_faces[0] in shellf]
mid = lambda e: 0.5 * (e.verts[0].co.z + e.verts[1].co.z)
mouthloops = [l for l in ([e for e in mouthedges if mid(e) >= 0.692], [e for e in mouthedges if mid(e) < 0.692]) if l]
info = []
welded = 0
for lp in sorted(mouthloops, key=lambda lp: -max(v.co.z for e in lp for v in e.verts)):
    sv = list({v for e in lp for v in e.verts})
    half = max(abs(v.co.x) for v in sv)
    cen = [v for v in sv if abs(v.co.x) < 0.3 * half]
    ends = [v for v in sv if abs(v.co.x) > 0.85 * half]
    zc = sum(v.co.z for v in cen) / len(cen)
    zend = sum(v.co.z for v in ends) / len(ends)
    yc = sum(v.co.y for v in cen) / len(cen)
    yend = sum(v.co.y for v in ends) / len(ends)
    for v in sv:
        u = abs(v.co.x) / half
        v.co.z = zc + (zend - zc) * u * u
        v.co.y = yc + (yend - yc) * u * u
    n0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=sv, dist=0.0016)
    welded += n0 - len(bm.verts)
    info.append({'edges': len(lp), 'half_cm': round(half * 100, 2), 'z_gltf': round(zc + LIFT, 4), 'corner_mm': round((zend - zc) * 1000, 2)})
lipA = info[0] if info else {'half_cm': 0, 'z_gltf': 0, 'corner_mm': 0}
half, zc, zend = lipA['half_cm'] / 100, lipA['z_gltf'] - LIFT, lipA['z_gltf'] - LIFT + lipA['corner_mm'] / 1000
yc = -0.06
slit = mouthloops
bm.verts.ensure_lookup_table()
# relax the lips' depth again
shell = {v for f in bm.faces if f[hl] and not (hn and f[hn]) for v in f.verts}
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
        new[v] = v.co.y + (sum(n.co.y for n in nb) / len(nb) - v.co.y) * 0.6 * x
    for v, y in new.items():
        v.co.y = max(y, y0[v])
for v in W:
    if abs(v.co.x) < 1e-5:
        v.co.x = 0.0
line = []
bm.to_mesh(me); bm.free()
json.dump({'half': half, 'zc_gltf': zc + LIFT, 'zend_gltf': zend + LIFT, 'loops': info}, open(OUT.rsplit('/work/', 1)[0] + '/work/mouth_line.json', 'w'))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('MOUTHCLOSE', {'inner_dropped': len(drop), 'loops': info, 'welded': welded})
