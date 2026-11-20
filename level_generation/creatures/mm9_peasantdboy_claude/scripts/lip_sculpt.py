"""Subtle child's lips sculpted into the face shell around the painted lip line (fifth pass, orchestrator: the painted mouth
read as a sticker on a flat face; no lips in profile). The shell is sparse there (vertices 3-5 mm apart), so the mouth
patch (head faces within |x| < 3.2 cm, 2.2 cm around the line, front) is first subdivided twice (UVs and weights
interpolated: the head stays rigid), then displaced along -y (forward) by a sum of soft profiles about the lip line L
(rest z 0.6936), all scaled by t = 1 - (|x| / HALF)^2 across the mouth:
  upper lip +1.0 mm (centre 2.2 mm above L), lower lip +1.8 mm (3 mm below L, a rounded underside), a groove at the line
  -0.4 mm, the mentolabial dip -0.6 mm (8 mm below L), a philtrum groove -0.3 mm (|x| < 4 mm, 4-12 mm above L), the corners
  tucked back -0.8 mm. (Defaults after trials: no subdivision and no base smoothing: subdividing put creases at the patch border and
depth-only smoothing dented the oblique cheeks; the existing vertices are 1-6 mm apart along the midline, enough for
these profiles.) Positions only. Args: <in blend> <out blend>"""
import bpy, bmesh, sys, math
a = sys.argv[sys.argv.index('--') + 1:]
L, HALF = 0.6936, 0.0235
import os
SUBDIV = int(os.environ.get('SUBDIV', '0'))
SMOOTH = int(os.environ.get('SMOOTH', '0'))
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me)
hl = bm.faces.layers.int['head']
inpatch = lambda p: abs(p.x) < 0.032 and abs(p.z - L) < 0.022 and p.y < -0.04
faces = [f for f in bm.faces if f[hl] and all(inpatch(v.co) for v in f.verts)]
edges = list({e for f in faces for e in f.edges})
n0 = len(bm.verts)
for _ in range(SUBDIV):
    res = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
    faces = [f for f in bm.faces if f[hl] and all(inpatch(v.co) for v in f.verts)]
    edges = list({e for f in faces for e in f.edges})
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
for f in bm.faces:
    if f[hl] and all(inpatch(v.co) for v in f.verts):
        f.smooth = True
# smooth base: Meshy's (relaxed) lip relief and the subdivided facets are evened out on the depth first, weighted to fade
# at the patch border, so the sculpted profile is the only lip shape
def fadew(p):
    return max(0.0, min(1.0, (0.032 - abs(p.x)) / 0.010, (0.022 - abs(p.z - L)) / 0.010))
pv = [v for v in {v for f in bm.faces if f[hl] for v in f.verts if inpatch(v.co)}]
pset = set(pv)
for _ in range(SMOOTH):
    new = {}
    for v in pv:
        w = fadew(v.co)
        if w <= 0:
            continue
        nb = [e.other_vert(v) for e in v.link_edges]
        if len(nb) < 3:
            continue
        new[v] = v.co.y + (sum(n.co.y for n in nb) / len(nb) - v.co.y) * 0.5 * w
    for v, y in new.items():
        v.co.y = y
g = lambda x, s: math.exp(-(x / s) ** 2)
moved = 0; mx = 0.0
for v in {v for f in bm.faces if f[hl] for v in f.verts if inpatch(v.co)}:
    p = v.co
    u = abs(p.x) / HALF
    t = max(0.0, 1 - u * u)
    dz = p.z - L
    d = 0.0010 * t ** 0.7 * g(dz - 0.0022, 0.0018)          # upper lip
    d += 0.0018 * t ** 0.7 * g(dz + 0.0030, 0.0024)         # lower lip
    d -= 0.0004 * t * g(dz, 0.0006)                          # where they meet
    d -= 0.0006 * t * g(dz + 0.0080, 0.0022)                 # mentolabial dip
    if abs(p.x) < 0.004 and 0.004 < dz < 0.012:
        d -= 0.0003 * (1 - abs(p.x) / 0.004) * math.sin(math.pi * (dz - 0.004) / 0.008)   # philtrum
    d -= 0.0008 * g(u - 1.0, 0.18) * g(dz, 0.004)           # corners tucked
    # fade at the patch border so the edit meets the untouched face
    fade = min(1.0, (0.032 - abs(p.x)) / 0.010, (0.022 - abs(dz)) / 0.010)
    d *= max(0.0, fade)
    p.y -= d
    moved += abs(d) > 1e-6; mx = max(mx, abs(d))
for v in bm.verts:
    if abs(v.co.x) < 1e-6:
        v.co.x = 0.0
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('LIPSCULPT', {'new_verts': len(me.vertices) - n0, 'moved': moved, 'max_mm': round(mx * 1000, 2)})
