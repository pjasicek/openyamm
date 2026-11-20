"""Body corrections on the Smart Topology parts before the head graft (user review 2026-10-30: "the arms are too thin",
"check the symmetry", "the chest is positioned too low"). work/st_v0_parts.blend -> work/st_v0_fixed_parts.blend.
- Symmetry: the torso missed its own mirror image by up to 18 mm (p90 13 mm at the bust, the bust 3 cm off centre).
  Every vertex of the body parts moves to the mean of itself and the mirror of its nearest point on the mirrored
  surface (all body parts together, so the two leg shells match each other); SYM_PASSES passes.
- Bust: the front of the torso around the bust apex (z BUST_Z) rises BUST_LIFT with a Gaussian falloff in height
  (BUST_SIGMA), fading out towards the sides and the back, so the upper chest shortens and the waist stays.
- Arms: the bare arms were 16 cm round at mid-forearm and 9-12 cm at the wrist (a grown woman: ~23 / 15 cm). Ring
  centres along each arm (joints from work/joints_final.json of the first rig); see the arm section below.
Args: none (settings below)"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
C = json.load(open(os.path.join(common.PROJECT, 'creature.json')))['body_fix']
SYM_PASSES = C.get('sym_passes', 2)
BUST_Z, BUST_SIGMA, BUST_LIFT = C['bust_z'], C.get('bust_sigma', 0.06), C['bust_lift']
# the joints are frozen on first use (work/body_fix_joints.json): every rig run rewrites joints_final.json, and arms
# measured from new joints no longer matched the mesh the body retexture was painted on
JF = os.path.join(common.WORK, 'body_fix_joints.json')
if not os.path.exists(JF):
    json.dump(json.load(open(os.path.join(common.WORK, 'joints_final.json'))), open(JF, 'w'), indent=1)
J = json.load(open(JF))['joints']
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st_v0_parts.blend'))
BODY = [bpy.data.objects[f'P{i:02d}'] for i in C['body_parts']]
SKIN = bpy.data.objects[f"P{C['arm_part']:02d}"]


def all_co():
    return [np.array([tuple(v.co) for v in o.data.vertices]) for o in BODY]


# ---- symmetry -------------------------------------------------------------------------------------------------------
for it in range(SYM_PASSES):
    cos = all_co()
    verts = np.concatenate(cos); polys = []; off = 0
    for o, c in zip(BODY, cos):
        polys += [tuple(i + off for i in p.vertices) for p in o.data.polygons]; off += len(c)
    tree = BVHTree.FromPolygons([Vector(v) for v in verts], polys)
    moved = []
    for o, c in zip(BODY, cos):
        for v, p in zip(o.data.vertices, c):
            loc = tree.find_nearest(Vector((-p[0], p[1], p[2])))[0]
            m = np.array((-loc.x, loc.y, loc.z))
            new = (p + m) / 2
            moved.append(np.linalg.norm(new - p)); v.co = Vector(new)
    print('BODYFIX symmetry pass', it + 1, 'moved mm p50 %.1f p90 %.1f max %.1f' % (
        np.median(moved) * 1000, np.percentile(moved, 90) * 1000, max(moved) * 1000))

# ---- bust -----------------------------------------------------------------------------------------------------------
co = np.array([tuple(v.co) for v in SKIN.data.vertices])
torso = (np.abs(co[:, 0]) < 0.2) & (co[:, 2] > BUST_Z - 0.2) & (co[:, 2] < BUST_Z + 0.2)
cy = (co[torso, 1].min() + co[torso, 1].max()) / 2
w = np.exp(-((co[:, 2] - BUST_Z) / BUST_SIGMA) ** 2)
w *= np.clip((cy - co[:, 1]) / 0.04, 0, 1)                    # the front half, fading over 4 cm at the sides
w *= np.exp(-np.maximum(np.abs(co[:, 0]) - 0.11, 0) ** 2 / 0.03 ** 2)   # not the arms or the armpits
for v, k in zip(SKIN.data.vertices, w):
    v.co.z += BUST_LIFT * k
print('BODYFIX bust lifted', int((w > 0.05).sum()), 'verts, max', round(BUST_LIFT * float(w.max()) * 100, 2), 'cm')

# ---- cleavage (user review 3: "the cleavage looks strange"): the chest was one smooth mound of 2 cm edges with a
# 4-edge hole at the centre, and Meshy painted a crease onto it. The hole is filled, the decolletage subdivided once
# and a valley pressed in: depth CL_DEPTH at the midline, Gaussian across (CL_WIDTH), full from just above the
# neckline (CL_Z0) to the bust apex, fading out above it by CL_Z1; front-facing skin only.
import bmesh
CL = C.get('cleavage')
if CL:
    bm = bmesh.new(); bm.from_mesh(SKIN.data)
    filled = []                                       # small holes closed by merging their rim to its centre (a fill
    edges_b = {e for e in bm.edges if e.is_boundary}   # made a back-facing pocket)
    while edges_b:
        e = edges_b.pop(); loop = {e}; st = [e]
        while st:
            x = st.pop()
            for v in x.verts:
                for y in v.link_edges:
                    if y in edges_b:
                        edges_b.discard(y); loop.add(y); st.append(y)
        vs = list({v for x in loop for v in x.verts})
        if len(loop) <= CL.get('fill_sides', 6):
            c = sum((v.co for v in vs), Vector()) / len(vs)
            bmesh.ops.pointmerge(bm, verts=vs, merge_co=c); filled.append(len(loop))
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    region = [f for f in bm.faces if all(abs(v.co.x) < CL['box_x'] and v.co.y < CL['front_y'] and
                                         CL['z0'] - 0.04 < v.co.z < CL['z1'] + 0.03 for v in f.verts)]
    edges = list({e for f in region for e in f.edges})
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True, smooth=0.5)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.normal_update()
    pressed = 0
    for v in bm.verts:
        if abs(v.co.x) > 3 * CL['width'] or v.normal.y > -0.4 or not (CL['z0'] - 0.015 < v.co.z < CL['z1']):
            continue
        zt = min(1.0, (v.co.z - (CL['z0'] - 0.015)) / 0.03)
        zt *= min(1.0, max(0.0, (CL['z1'] - v.co.z) / (CL['z1'] - CL['apex'])))
        zt = zt * zt * (3 - 2 * zt)
        w = math.exp(-(v.co.x / CL['width']) ** 2) * zt
        if w > 1e-3:
            v.co.y += CL['depth'] * w; pressed += 1
    bm.to_mesh(SKIN.data); bm.free()
    print('BODYFIX cleavage: holes filled', len(filled), 'region faces subdivided', len(region), 'verts pressed', pressed)

# ---- arms -----------------------------------------------------------------------------------------------------------
# rings: the skin shell sliced perpendicular to the shoulder -> elbow -> wrist path every 1 cm; per slice the closed
# loop nearest the path gives the arm's true centre and mean radius (the bones do not run through the middle).
# Each arm vertex beyond the sleeve hem (path parameter HEM) moves away from its slice centre by target / measured
# radius (targets linear hem -> elbow -> wrist, 1.0-1.8), fading back to 1 over the first HAND_FADE m of the hand;
# vertices farther than 1.5x the ring radius from the centre (the sleeve's puff) are left alone.
import bmesh
from mathutils.geometry import intersect_point_line
HEM, TGT = C['arm_hem'], C['arm_radius']               # target ring radius (m) at the hem, the elbow, the wrist
HAND_FADE = C.get('hand_fade', 0.04)
bm0 = bmesh.new(); bm0.from_mesh(SKIN.data)


def rings_at(p, n):
    bm = bm0.copy()
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(p), plane_no=Vector(n))
    edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in edges:
        x, y = e.verts; adj.setdefault(x, []).append(y); adj.setdefault(y, []).append(x)
    seen, out = set(), []
    for v in adj:
        if v in seen:
            continue
        st, comp = [v], []
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x.co.copy()); st += adj[x]
        if len(comp) >= 6:
            c = np.array([tuple(q) for q in comp]); out.append((c.mean(0), float(np.linalg.norm(c - c.mean(0), axis=1).mean())))
    bm.free()
    return out


co = np.array([tuple(v.co) for v in SKIN.data.vertices]); new = co.copy()
for s, sg in (('L', 1), ('R', -1)):
    S, E, Wr = (np.array(J[f'{s}_{b}']) for b in ('UpperArm', 'Forearm', 'Hand'))
    L1, L2 = np.linalg.norm(E - S), np.linalg.norm(Wr - E); Lt = L1 + L2
    def path(u):                                       # u over the whole arm: 0 shoulder, 1 wrist
        d = u * Lt
        return (S + (E - S) * d / L1, (E - S) / L1) if d <= L1 else (E + (Wr - E) * (d - L1) / L2, (Wr - E) / L2)
    us = np.arange(HEM, 1.0001, 0.01 / Lt)
    cen, rad, tang = [], [], []
    for u in us:
        p, n = path(u)
        rs = [r for r in rings_at(p, n) if np.linalg.norm(r[0] - p) < 0.07 and np.sign(r[0][0]) == sg]
        if rs:
            c, r = min(rs, key=lambda r: np.linalg.norm(r[0] - p)); cen.append(c); rad.append(r); tang.append(n)
        else:
            cen.append(None); rad.append(None); tang.append(n)
    ok = [i for i, c in enumerate(cen) if c is not None]
    cen = np.array([cen[i] if cen[i] is not None else cen[min(ok, key=lambda k: abs(k - i))] for i in range(len(us))])
    rad = np.array([rad[i] if rad[i] is not None else rad[min(ok, key=lambda k: abs(k - i))] for i in range(len(us))])
    k = np.ones(5) / 5                                 # smooth the centre line and the radii a little
    cen = np.stack([np.convolve(np.pad(cen[:, j], 2, mode='edge'), k, 'valid') for j in range(3)], 1)
    rad = np.convolve(np.pad(rad, 2, mode='edge'), k, 'valid')
    ue = L1 / Lt
    fac = np.clip(np.interp(us, [HEM, ue, 1.0], TGT) / rad, 1.0, 1.8)
    side = np.sign(co[:, 0]) == sg
    pushed = 0
    for i in np.where(side)[0]:
        # parameter of the vertex: nearest centre-line point (within the sampled range, or a little past the wrist)
        dd = np.linalg.norm(cen - co[i], axis=1); j = int(np.argmin(dd))
        if dd[j] > 0.09:
            continue
        tj = np.array(tang[j]); along = (co[i] - cen[j]) @ tj
        if j == 0 and along < 0:
            continue                                   # above the hem
        radial = (co[i] - cen[j]) - tj * along
        if np.linalg.norm(radial) > 1.5 * rad[j]:
            continue                                   # the sleeve's puff
        f = fac[j]
        if j == len(us) - 1 and along > 0:             # into the hand
            f = 1 + (f - 1) * max(0.0, 1 - along / HAND_FADE)
        if f > 1.0001:
            new[i] = cen[j] + tj * along + radial * f; pushed += 1
    print('BODYFIX arm', s, 'rings', len(ok), 'of', len(us), 'radius mm at hem/elbow/wrist %.0f/%.0f/%.0f' % (
        rad[0] * 1000, rad[int(np.argmin(np.abs(us - ue)))] * 1000, rad[-1] * 1000), 'verts pushed', pushed)
bm0.free()
for v, p in zip(SKIN.data.vertices, new):
    v.co = Vector(p)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'st_v0_fixed_parts.blend'))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
for o in bpy.data.objects:
    o.hide_render = o.type == 'MESH' and o not in BODY
common.render_views(os.path.join(common.REVIEW, 'bodyfix'), 0.95, 1.2, views=('front', 'left', 'three_quarter'),
                    resolution=(600, 700))
