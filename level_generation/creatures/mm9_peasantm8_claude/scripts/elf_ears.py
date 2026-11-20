"""Elf ears on Forad's head (PeasantM8d = ForadDarre mesh + elf ears, MM9 ear tip ~4 cm up/back/out of the human ear).
Vertex moves only (no new vertices: UVs, weights and part numbering stay): each ear (the lateral HeadUV islands of the
master, the right one completed by mirroring the left) is drawn up, back and out into a point. A vertex moves by
tip * s(t) * w, t = its height in the ear (0 bottom .. 1 top), s = smoothstep(T0, 1, t) ** P, w = 0 on the root (ear
vertices shared with skull faces) rising to 1 after HOPS edges; the upper ear narrows front-to-back toward the tip line.
Also usable on another mesh with the same vertices in the same positions (the Meshy upload): mode `upload`.
Args (Blender): master <in blend> <out blend> <report json> [preview png]  |  upload <in glb> <out glb> <report json>
"""
import bpy, bmesh, sys, os, json, collections
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
MODE = argv[0]
E = lambda k, d: float(os.environ.get(k, d))
TIP = np.array([E('TIPX', 0.022), E('TIPY', 0.018), E('TIPZ', 0.032)])   # x outward (per side), y back, z up
FLARE = E('FLARE', 0.006)                                              # extra outward at the top of the ear
T0, PWR, HOPS, TAPER = E('T0', 0.0), E('PWR', 1.0), E('HOPS', 2), E('TAPER', 0.5)
CX = -0.017


def ear_sets(P, L, ls, lt, head, huv):
    faces = list(np.where(head)[0]); U = np.round(huv * 1e5).astype(np.int64)
    par = {f: f for f in faces}
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    seen = {}
    for f in faces:
        for li in range(ls[f], ls[f] + lt[f]):
            k = (L[li], U[li, 0], U[li, 1])
            if k in seen:
                a, b = find(f), find(seen[k])
                if a != b: par[a] = b
            else:
                seen[k] = f
    g = collections.defaultdict(list)
    for f in faces: g[find(f)].append(f)
    ear = {-1: set(), 1: set()}
    for isl in g.values():
        vs = np.unique(np.concatenate([L[ls[f]:ls[f] + lt[f]] for f in isl])); c = P[vs].mean(0)
        if len(isl) < 80 and abs(c[0] - CX) > 0.06 and 0.70 < c[2] < 0.86:
            ear[int(np.sign(c[0] - CX))] |= set(vs.tolist())
    hv = np.unique(np.concatenate([L[ls[f]:ls[f] + lt[f]] for f in faces]))
    R = np.array([v for v in hv if P[v, 0] > CX]); M = P[sorted(ear[-1])].copy(); M[:, 0] = 2 * CX - M[:, 0]
    dm = np.linalg.norm(M[:, None, :] - P[R][None, :, :], axis=2); ii = dm.argmin(1); dd = dm.min(1)
    ear[1] |= set(R[ii[dd < 0.006]].tolist())
    return ear


def displacement(P, L, ls, lt, head, huv):
    ear = ear_sets(P, L, ls, lt, head, huv)
    nb = collections.defaultdict(set); fof = collections.defaultdict(list)
    for f in range(len(ls)):
        vs = L[ls[f]:ls[f] + lt[f]]
        for k in range(len(vs)):
            a, b = vs[k], vs[(k + 1) % len(vs)]; nb[a].add(b); nb[b].add(a)
        for v in vs: fof[v].append(f)
    D = np.zeros_like(P); rep = {}
    for s, E in ear.items():
        E = sorted(E); Es = set(E)
        root = [v for v in E if any(not all(u in Es for u in L[ls[f]:ls[f] + lt[f]]) for f in fof[v])]
        hop = {v: 0 for v in root}; q = collections.deque(root)
        while q:
            x = q.popleft()
            for y in nb[x]:
                if y in Es and y not in hop:
                    hop[y] = hop[x] + 1; q.append(y)
        Q = P[E]; z0, z1 = Q[:, 2].min(), Q[:, 2].max(); yc = np.median(Q[:, 1])
        tip = TIP * np.array([s, 1, 1])
        for v in E:
            t = np.clip((P[v, 2] - z0) / (z1 - z0), 0, 1)
            u = np.clip((t - T0) / (1 - T0), 0, 1); sm = (u * u * (3 - 2 * u)) ** PWR
            w = min(1.0, hop.get(v, HOPS) / HOPS)
            d = tip * sm * w
            d[0] += s * FLARE * t * w
            d[1] += (yc - P[v, 1]) * TAPER * sm * w
            D[v] = d
        rep[s] = dict(verts=len(E), root=len(root), z=[float(z0), float(z1)], max_cm=float(np.linalg.norm(D[E], axis=1).max() * 100))
    return D, rep


def mesh_arrays(me, mw):
    P = np.array([mw @ v.co for v in me.vertices])
    L = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', L)
    ls = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get('loop_start', ls)
    lt = np.zeros(len(me.polygons), np.int32); me.polygons.foreach_get('loop_total', lt)
    return P, L, ls, lt


if MODE == 'master':
    IN, OUT, REP = argv[1:4]
    bpy.ops.wm.open_mainfile(filepath=IN)
    body = bpy.data.objects['Body']; rig = body.parent
    if rig.animation_data: rig.animation_data.action = None
    for b in rig.pose.bones: b.matrix_basis.identity()
    me = body.data
    P, L, ls, lt = mesh_arrays(me, body.matrix_world)
    hd = np.zeros(len(ls), np.int32); me.attributes['head'].data.foreach_get('value', hd)
    huv = np.zeros(len(me.loops) * 2); me.uv_layers['HeadUV'].data.foreach_get('uv', huv)
    D, rep = displacement(P, L, ls, lt, hd, huv.reshape(-1, 2))
    inv = np.array(body.matrix_world.inverted().to_3x3())
    for i in np.where(np.abs(D).sum(1) > 0)[0]:
        me.vertices[i].co += Vector(inv @ D[i])
    me.update()
    # PeasantM8d wears no necklace: Forad's bead parts (small loose parts at the collar, < 40 vertices, < 3 cm, below
    # z 0.70) go, and Meshy's eyeball cups (Forad's export_fix drop_parts 6, 11: the two loose head parts at eye height)
    # are dropped here instead of at export, so the part numbering no longer matters (head_pm8d.json drops nothing).
    if os.environ.get('DROP', '1') == '1':
        bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
        comp = -np.ones(len(bm.verts), np.int32); cid = 0
        for v in bm.verts:
            if comp[v.index] >= 0: continue
            st = [v]; comp[v.index] = cid
            while st:
                x = st.pop()
                for e in x.link_edges:
                    y = e.other_vert(x)
                    if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
            cid += 1
        P2 = P + D; drop = []
        for c in range(cid):
            idx = np.where(comp == c)[0]; Q = P2[idx]; ext = np.linalg.norm(Q.max(0) - Q.min(0))
            eye = 0.76 < Q[:, 2].mean() < 0.81 and Q[:, 1].mean() < -0.05 and len(idx) < 80
            bead = len(idx) < 40 and ext < 0.03 and Q[:, 2].max() < 0.70
            if eye or bead: drop.append((c, len(idx), 'eye' if eye else 'bead'))
        dset = {c for c, _, _ in drop}
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if comp[v.index] in dset], context='VERTS')
        bm.to_mesh(me); bm.free(); me.update()
        rep['dropped'] = {'eyes': sum(1 for d in drop if d[2] == 'eye'), 'beads': sum(1 for d in drop if d[2] == 'bead'),
                          'verts': int(sum(d[1] for d in drop))}
    np.save(os.path.splitext(REP)[0] + '_disp.npy', D)
    json.dump(rep, open(REP, 'w'), indent=1); print('EARS', rep)
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    if len(argv) > 4:
        sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
        sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
        sc.render.resolution_x = sc.render.resolution_y = 400
        w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.4, 0.4, 0.4)
        cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.34
        cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
        c = Vector((CX, 0.01, 0.77))
        ims = []
        for k, dv in enumerate([(0, -1, 0), (-1, 0, 0), (1, 0, 0), (-1, 1, 0.3), (0, 1, 0)]):
            dv = Vector(dv).normalized(); cam.location = c + dv * 3
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            fp = argv[4] + f'_{k}.png'; sc.render.filepath = fp; bpy.ops.render.render(write_still=True); ims.append(fp)
