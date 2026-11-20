"""Meshy left the ring fingers of both hands as blunt stubs without claws. Grow a claw out of each stub:
  - the adjacent finger's claw (connected ivory-textured patch) gives direction a, length, curl and the texture,
  - the stub's end cap (faces furthest along a) is removed, leaving its rim loop,
  - rings extend the rim's own cross-section along a curved centreline (curl toward the neighbour's), tapering to a
    point, so the finger flows into the claw like the others,
  - UVs come from the neighbour claw: each new vertex takes the UV of the neighbour-claw vertex nearest in
    (position along the claw, angle around it), so it gets the same ivory texture (the texture set is unchanged),
  - new vertices take the stub tip's weights.
Runs on work/rig_uv.blend after uv_export.py (the UV layout must not change); saves work/rig_claws.blend."""
import bpy, bmesh, os, math, heapq
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUBS = {'Left': Vector((0.435, -0.340, 0.676)), 'Right': Vector((-0.471, -0.387, 0.629))}   # stub tips (rest)
IVORY = 0.36                        # min channel of ivory claw texels (Meshy shaded some claws darker)
CAP_DEPTH, LENGTH_SCALE, RINGS = 0.015, 0.85, 9
mesh = bpy.data.objects['Demon']
img = bpy.data.images.load(os.path.join(HERE, 'textures', 'wdm_basecolor.png'))
img.colorspace_settings.name = 'Non-Color'
W, H = img.size
tex = np.array(img.pixels[:], np.float32).reshape(H, W, 4)[..., :3]


def ivory(uv):
    x = min(W - 1, max(0, int(uv[0] * (W - 1)))); y = min(H - 1, max(0, int(uv[1] * (H - 1))))
    return tex[y, x].min() > IVORY


def geodesic(start, allowed, limit):
    dist = {start.index: 0.0}; h = [(0.0, start.index, start)]
    while h:
        d, _, a = heapq.heappop(h)
        if d > dist[a.index] or d > limit:
            continue
        for e in a.link_edges:
            b = e.other_vert(a); nd = d + e.calc_length()
            if b.index in allowed and nd < dist.get(b.index, 1e9):
                dist[b.index] = nd; heapq.heappush(h, (nd, b.index, b))
    return dist


def frame(a):
    """Two unit vectors perpendicular to a."""
    t = Vector((0, 0, 1)) if abs(a.z) < 0.9 else Vector((1, 0, 0))
    e1 = a.cross(t).normalized(); return e1, a.cross(e1).normalized()


bm = bmesh.new(); bm.from_mesh(mesh.data)
uvl = bm.loops.layers.uv.active; dl = bm.verts.layers.deform.active
for side, stub in STUBS.items():
    bm.verts.ensure_lookup_table(); bm.verts.index_update(); bm.faces.ensure_lookup_table(); bm.faces.index_update()
    gi = mesh.vertex_groups[f'mixamorig:{side}Hand'].index
    hand = {v.index for v in bm.verts if v[dl].get(gi, 0.0) > 0.3}
    region = {v.index for v in bm.verts if (v.co - stub).length < 0.16}
    tip = min((bm.verts[i] for i in hand), key=lambda v: (v.co - stub).length)
    # neighbour claw: nearest sizeable ivory patch
    claw_faces = [f for f in bm.faces if all(v.index in region for v in f.verts)
                  and all(ivory(l[uvl].uv) for l in f.loops)]
    fset = set(claw_faces); seen = set(); best = None
    for f in claw_faces:
        if f in seen:
            continue
        st = [f]; comp = []; seen.add(f)
        while st:
            x = st.pop(); comp.append(x)
            for e in x.edges:
                for g in e.link_faces:
                    if g in fset and g not in seen:
                        seen.add(g); st.append(g)
        vs = {v for x in comp for v in x.verts}
        bnd = [v for v in vs if any(g not in comp for g in v.link_faces)]
        if len(comp) < 20 or not bnd or tip in vs:
            continue
        B = sum((v.co for v in bnd), Vector()) / len(bnd)
        far = max(vs, key=lambda v: (v.co - B).length); L = (far.co - B).length
        d = (B - tip.co).length
        if L > 0.05 and 0.012 < d < 0.08 and (best is None or d < best[0]):
            best = (d, comp, vs, B, far.co.copy(), L)
    _, comp, vs, _, _, _ = best
    # neighbour claw axis: principal axis of the patch, oriented away from the wrist
    pts = np.array([tuple(v.co) for v in vs]); m = pts.mean(0)
    pa = np.linalg.svd(pts - m)[2][0]
    wrist = np.array(mesh.matrix_world.inverted() @ (bpy.data.objects['Demon_Rig'].matrix_world
                     @ bpy.data.objects['Demon_Rig'].data.bones[f'mixamorig:{side}Hand'].head_local))
    t = (pts - m) @ pa
    if np.linalg.norm(pts[np.argmax(t)] - wrist) < np.linalg.norm(pts[np.argmin(t)] - wrist):
        pa = -pa; t = -t
    t0, t1 = t.min(), t.max()
    Cb = Vector(pts[t < t0 + 0.15 * (t1 - t0)].mean(0))
    Cm = Vector(pts[(t > t0 + 0.35 * (t1 - t0)) & (t < t0 + 0.5 * (t1 - t0))].mean(0))
    T = Vector(pts[np.argmax(t)]); B = Cb; L = (T - Cb).length
    a = (Cm - Cb).normalized()
    along = (T - B).dot(a); perp = (T - B) - a * along
    print('NEIGHBOUR', side, 'a', tuple(round(x, 2) for x in a), 'along %.3f perp %.3f' % (along, perp.length))
    e1, e2 = frame(a)
    curl_dir = perp.normalized() if perp.length > 1e-6 else e1
    bend = min(0.6, perp.length / max(along, 0.02))
    # neighbour-claw UV lookup in (u along, angle around)
    samples = []                                       # one UV per neighbour-claw face (consistent island)
    for x in comp:
        r = x.calc_center_median() - B
        uvc = sum((l[uvl].uv for l in x.loops), Vector((0.0, 0.0))) / len(x.loops)
        samples.append((r.dot(a) / along, math.atan2(r.dot(e2), r.dot(e1)), uvc))
    S_u = np.array([s[0] for s in samples]); S_a = np.array([s[1] for s in samples])

    def uv_for(u, ang):
        da = np.abs((S_a - ang + math.pi) % (2 * math.pi) - math.pi)
        return samples[int(np.argmin(np.abs(S_u - u) * 4.0 + da * 0.05))][2]
    # stub end cap: faces whose vertices all lie within CAP_DEPTH of the furthest point along a
    near = [bm.verts[i] for i in geodesic(tip, hand, 0.03)]
    tmax = max(v.co.dot(a) for v in near)
    cap_v = {v for v in near if v.co.dot(a) > tmax - CAP_DEPTH}
    cap_f = [f for f in {f for v in cap_v for f in v.link_faces} if all(v in cap_v for v in f.verts)]
    bmesh.ops.delete(bm, geom=cap_f, context='FACES_ONLY')
    rim_e = [e for e in bm.edges if e.is_boundary and all(v in cap_v for v in e.verts)]
    nb = {}
    for e in rim_e:
        x, y = e.verts; nb.setdefault(x, []).append(y); nb.setdefault(y, []).append(x)
    start = next(iter(nb)); loop = [start]; prev = None
    while True:
        cur = loop[-1]; nxt = [v for v in nb[cur] if v is not prev]
        if not nxt or nxt[0] is start or len(loop) > len(nb):
            break
        prev = cur; loop.append(nxt[0])
    weights = dict(tip[dl])
    C0 = sum((v.co for v in loop), Vector()) / len(loop)
    length = L * LENGTH_SCALE
    rings = [loop]
    for k in range(1, RINGS + 1):
        u = k / (RINGS + 1)
        c = C0 + a * length * u + curl_dir * bend * length * u * u
        shrink = (1.0 - u) ** 0.55                    # neighbour claws stay thick, then taper fast
        ring = []
        for v in loop:
            nv = bm.verts.new(c + (v.co - C0) * shrink)
            for g, w in weights.items():
                nv[dl][g] = w
            ring.append(nv)
        rings.append(ring)
    apex = bm.verts.new(C0 + a * length + curl_dir * bend * length)
    for g, w in weights.items():
        apex[dl][g] = w
    n = len(loop)
    # winding: the remaining finger face on each rim edge must be traversed opposite to the new face
    rim_face = next(f for f in loop[0].link_faces)
    fv = list(rim_face.verts); i0 = fv.index(loop[0])
    flip = fv[(i0 + 1) % len(fv)] is loop[1]
    new_faces = []
    for k in range(RINGS):
        for j in range(n):
            q = [rings[k][j], rings[k][(j + 1) % n], rings[k + 1][(j + 1) % n], rings[k + 1][j]]
            new_faces.append(bm.faces.new(q[::-1] if flip else q))
    for j in range(n):
        t = [rings[-1][j], rings[-1][(j + 1) % n], apex]
        new_faces.append(bm.faces.new(t[::-1] if flip else t))
    for f in new_faces:
        f.smooth = True
        r = f.calc_center_median() - C0
        uv = uv_for(0.15 + 0.85 * min(1.0, r.dot(a) / max(length, 1e-6)), math.atan2(r.dot(e2), r.dot(e1)))
        for l in f.loops:
            l[uvl].uv = uv
    loose = [v for v in cap_v if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    print('CLAW', side, 'rim verts', n, 'of', len(nb), 'cap faces removed', len(cap_f), 'length %.3f' % length,
          'bend %.2f' % bend)
bm.normal_update()
bm.to_mesh(mesh.data); bm.free(); mesh.data.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_claws.blend'))
print('SAVED claws')
