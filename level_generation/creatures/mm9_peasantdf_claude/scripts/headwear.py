"""Per-design headwear shape (coordinator review r4, 2026-11-02: the shared hair/hood shell read as a smooth egg from every
side, where MM9's four models show a loose bob (DF1), a draped kerchief (DF2) and pointed hoods with a brim framing the
face (DF3, DF4)). Positions only on the design's copy of the shared master: the face, rig, clips, UVs and paint stay.

1. MM9's covering surface: the design's own MM9 model (raw conversion, same frame as the master), moved by the fit's
   Head joint move, keeping only faces mostly weighted to the head or the hair chains (Head, Ponytail1, LF/RF_tail*)
   that lie more than FACE_GAP from our head's skin shell (MM9's face itself is left out).
2. Each vertex of our hair/hood loose part is cast radially from the head's centre (Head joint + 6.5 cm up) through
   the vertex against that surface (hits within REACH of the vertex); the displacement to the nearest hit times STRENGTH, Laplacian-smoothed over the shell (SMOOTH passes, so
   MM9's facets do not come through), moves the vertex. Vertices without a hit take the smoothed field only.
3. Optional braids (`braids=1`, DF3a): a tapered round braid along each hair-side chain (LF_tail -> LF_tail2 -> LF_tail3
   and on, the chain MM9 animates its braids with), rigid per segment on those bones, its HeadUV over the head set's free
   column (`braid_uv`, default u 0.82-0.98, v 0.05-0.55) where braid_paint.py paints a plait.
   Options drop=<m> (the hem lowered toward the shoulders at the back and sides) and peak=<m> (a hood point over the
   crown) shape what the ray cast cannot reach; shrink=<sx,sy> (r5) narrows the shell at the temples and the back bulge
   above the ears (never within 9 mm of the skull).
Args (Blender): <in blend> <out blend> <mm9 glb> <fit json> [strength 1.0] [reach 0.06] [smooth 4] [braids 0] [braid_uv u0,v0,u1,v1]"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, MM9, FIT = a[:4]
opt = dict(x.split('=', 1) for x in a[4:])
STRENGTH = float(opt.get('strength', 1.0)); REACH = float(opt.get('reach', 0.07)); SMOOTH = int(opt.get('smooth', 2))
FACE_GAP = 0.012
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; M = body.matrix_world; Mi = M.inverted()
move = Vector([x / 100.0 for x in json.load(open(FIT))['joint_moves_xyz_cm']['Bip01 Head']])
# ---- MM9 covering surface
existing = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MM9)
new = [o for o in bpy.data.objects if o not in existing]
mm = max((o for o in new if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
marm = next(o for o in new if o.type == 'ARMATURE')
if marm.animation_data: marm.animation_data.action = None
for pb in marm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
KEEP = ('Bip01 Head', 'Bip01 Ponytail1', 'LF_tail', 'LF_tail2', 'LF_tail3', 'RF_tail', 'RF_tail2', 'RF_tail3')
gi = {g.index for g in mm.vertex_groups if g.name in KEEP}
MP = [mm.matrix_world @ v.co + move for v in mm.data.vertices]
hw = [sum(g.weight for g in v.groups if g.group in gi) for v in mm.data.vertices]
# our head skin shell (head faces that are not the hair part) for the face test
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lk = bm.faces.layers.int['head']; lh = bm.faces.layers.int['hand']; lt = bm.faces.layers.int.get('twin')
comp = {}; parts = []
for v in bm.verts:
    if v in comp: continue
    st = [v]; comp[v] = len(parts); cur = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if o not in comp: comp[o] = len(parts); st.append(o); cur.append(o)
    parts.append(cur)
big = max(range(len(parts)), key=lambda i: len(parts[i]))
cand = [i for i in range(len(parts)) if i != big and len(parts[i]) > 200 and np.mean([(M @ v.co).z for v in parts[i]]) > 0.38]
hair = max(cand, key=lambda i: len(parts[i]))
hv = parts[hair]
skin_faces = [f for f in bm.faces if f[lk] and not f[lh] and not (lt and f[lt]) and comp[f.verts[0]] == big]
sk_bvh = BVHTree.FromPolygons([M @ v.co for v in bm.verts], [[v.index for v in f.verts] for f in skin_faces])
polys = []
for p in mm.data.polygons:
    if np.mean([hw[i] for i in p.vertices]) < 0.5: continue
    c = sum((MP[i] for i in p.vertices), Vector()) / len(p.vertices)
    loc, nrm, idx, dist = sk_bvh.find_nearest(c)
    if dist is not None and dist < FACE_GAP: continue
    polys.append(list(p.vertices))
cov = BVHTree.FromPolygons(MP, polys)
# ---- displacement of the hair part
idx = {v: k for k, v in enumerate(hv)}
D = np.zeros((len(hv), 3)); hit = np.zeros(len(hv), bool)
# v2 (clay sheet: casting along the vertex normals barely moved the egg): radial from the head's centre through each vertex,
# so the shell takes MM9's outline (the hood point, straight sides, the hem down at the shoulders)
HC = rig.matrix_world @ rig.data.bones['Bip01 Head'].head_local + Vector((0, 0.01, 0.065))
for k, v in enumerate(hv):
    p = M @ v.co; dvec = (p - HC)
    if dvec.length < 1e-6: continue
    dvec.normalize()
    h = cov.ray_cast(HC, dvec, 0.35)
    if h[0] is not None and (h[0] - p).length < REACH:
        D[k] = np.array(h[0] - p) * STRENGTH; hit[k] = True
nb = [[idx[e.other_vert(v)] for e in v.link_edges if e.other_vert(v) in idx] for v in hv]
for _ in range(SMOOTH):
    D2 = D.copy()
    for k in range(len(hv)):
        if nb[k]:
            D2[k] = 0.5 * D[k] + 0.5 * D[nb[k]].mean(0) if hit[k] else D[nb[k]].mean(0)
    D = D2
DROP = float(opt.get('drop', 0.0)); PEAK = float(opt.get('peak', 0.0))
SHRINK = [float(x) for x in opt['shrink'].split(',')] if 'shrink' in opt else None
CLEAR = float(opt.get('clear', 0.004))
def ss(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
newp = [M @ v.co + Vector(D[k].tolist()) for k, v in enumerate(hv)]
top = max(p.z for p in newp)
for k, v in enumerate(hv):
    p = newp[k]
    # v3: the hem falls to the shoulders at the back and sides (MM9's hoods and bob end there; ours ended at the nape)
    if DROP:
        p = p + Vector((0, 0, -DROP * ss((0.40 - p.z) / 0.06) * ss((p.y + 0.03) / 0.06)))
    # v3: the hood's point over the crown (DF3/DF4)
    if PEAK:
        p = p + Vector((0, PEAK * 0.3, PEAK)) * ss(1 - abs(p.x) / 0.055) * ss((p.z - (top - 0.06)) / 0.06)
    # r5 (coordinator: DF3/DF4 hoods read as big bulbs next to MM9's): the shell narrows at the temples (x) and loses some
    # of its back bulge (y behind the head joint) above the ears, never closer than 9 mm to the skull
    if SHRINK:
        w = ss((p.z - 0.34) / 0.08)
        q = Vector((HC.x + (p.x - HC.x) * (1 - (1 - SHRINK[0]) * w), p.y if p.y < HC.y else HC.y + (p.y - HC.y) * (1 - (1 - SHRINK[1]) * w), p.z))
        loc, nrm_, idx_, dist = sk_bvh.find_nearest(q)
        if dist is not None and dist < 0.009 and (q - loc).dot(nrm_) > -1:
            q = p.lerp(q, max(0.0, (dist - 0.003) / 0.006))
        p = q
    # r6: the widened temples/cheeks (face_widen.py) must stay under the hair/hood: keep the shell CLEAR outside the skin
    loc, nrm_, idx_, dist = sk_bvh.find_nearest(p)
    if dist is not None and CLEAR > 0:
        out = (p - loc).dot(nrm_)
        if out < CLEAR and dist < 0.03:
            p = p + nrm_ * (CLEAR - out)
    v.co = Mi @ p
rep = {'mm9_faces_kept': len(polys), 'hair_verts': len(hv), 'hit': int(hit.sum()), 'mean_move_cm': round(float(np.linalg.norm(D, axis=1).mean() * 100), 2),
       'max_move_cm': round(float(np.linalg.norm(D, axis=1).max() * 100), 2)}
# ---- braids
if opt.get('braids', '0') == '1':
    # the braids' own procedural plait texture in the head set's free column (braid_paint.py paints it there)
    u0, v0, u1, v1 = [float(x) for x in opt.get('braid_uv', '0.82,0.05,0.98,0.55').split(',')]
    uvh = bm.loops.layers.uv['HeadUV']; uvm = bm.loops.layers.uv['UVMap']
    dl = bm.verts.layers.deform.active
    names = [g.name for g in body.vertex_groups]
    for b in ('LF_tail', 'LF_tail2', 'LF_tail3', 'RF_tail', 'RF_tail2', 'RF_tail3'):   # fit_rig dropped empty groups
        if b not in names:
            body.vertex_groups.new(name=b); names.append(b)
    for chain in (('LF_tail', 'LF_tail2', 'LF_tail3'), ('RF_tail', 'RF_tail2', 'RF_tail3')):
        J = [rig.matrix_world @ rig.data.bones[n].head_local for n in chain]
        # start a little below the chain root (inside the hood edge), run past the last joint by the last segment
        pts = [J[0].lerp(J[1], 0.35), J[1], J[2], J[2] + (J[2] - J[1]) * 0.9]
        bones = [chain[0], chain[1], chain[2], chain[2]]
        NS, NR = 16, 6
        rings = []
        for i in range(NS + 1):
            t = i / NS * (len(pts) - 1); k = min(int(t), len(pts) - 2); f = t - k
            c = pts[k].lerp(pts[k + 1], f); d = (pts[k + 1] - pts[k]).normalized()
            r = 0.011 * (1.0 - 0.45 * i / NS) * (1.0 + 0.18 * math.sin(i * math.pi * 1.5) ** 2)   # plaits bulge
            side = d.cross(Vector((0, 1, 0))).normalized(); up = d.cross(side).normalized()
            ring = []
            for j in range(NR):
                ang = 2 * math.pi * j / NR
                vtx = bm.verts.new(Mi @ (c + (side * math.cos(ang) + up * math.sin(ang)) * r))
                b = bones[min(int(t + 0.5), len(bones) - 1)]
                vtx[dl][names.index(b)] = 1.0
                ring.append(vtx)
            rings.append(ring)
        for i in range(NS):
            for j in range(NR):
                q = [rings[i][j], rings[i][(j + 1) % NR], rings[i + 1][(j + 1) % NR], rings[i + 1][j]]
                fc = bm.faces.new(q)   # (reversed, check_winding found the closed braids inverted)
                fc[lk] = 1; fc[lh] = 0; fc.smooth = True
                fc.material_index = skin_faces[0].material_index
                for L, (ii, jj) in zip(fc.loops, [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]):
                    L[uvh].uv = (u0 + (u1 - u0) * jj / NR, v0 + (v1 - v0) * ii / NS)
                    L[uvm].uv = L[uvh].uv
        tip = bm.verts.new(Mi @ pts[-1]); tip[dl][names.index(bones[-1])] = 1.0
        for j in range(NR):
            fc = bm.faces.new([rings[-1][j], rings[-1][(j + 1) % NR], tip]); fc[lk] = 1; fc[lh] = 0; fc.smooth = True
            fc.material_index = skin_faces[0].material_index
            for L in fc.loops: L[uvh].uv = ((u0 + u1) / 2, v1); L[uvm].uv = L[uvh].uv
        root = bm.verts.new(Mi @ pts[0]); root[dl][names.index(bones[0])] = 1.0        # closed at the top too
        for j in range(NR):
            fc = bm.faces.new([rings[0][(j + 1) % NR], rings[0][j], root]); fc[lk] = 1; fc[lh] = 0; fc.smooth = True
            fc.material_index = skin_faces[0].material_index
            for L in fc.loops: L[uvh].uv = ((u0 + u1) / 2, v0); L[uvm].uv = L[uvh].uv
    rep['braids'] = {'uv_rect': [round(u0, 3), round(v0, 3), round(u1, 3), round(v1, 3)], 'faces_per_braid': 16 * 6 + 6}
for o in new:
    bpy.data.objects.remove(o)
bm.normal_update(); bm.to_mesh(me); me.update()
rep['tris'] = sum(len(p.vertices) - 2 for p in me.polygons)
print('HEADWEAR', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
