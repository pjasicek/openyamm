"""Revision 05 patch of the final Wyrm geometry (work/uv_final.blend -> work/uv_final_v5.blend), keeping every
existing UV so the Meshy v2 textures stay valid (user review 2026-10-13):
1. Holes: every open loop of up to 12 edges is closed with an explicitly built face (bmesh holes_fill silently left
   the chest junction and tail-base holes open), except the generated teeth bases (hidden in the gums) and the eye
   sockets (refilled by 2). New faces copy each vertex's UV from an adjacent face of the same material.
2. Eyes: the lumpy source eye pieces are replaced by clean ellipsoid eyeballs fitted to their bounding boxes (rigid on
   Head, WyrmHead material, part 5/6), mapped into an empty square of the head texture; compose paints them by
   position.
Also writes work/old_uv3d.npz (source revision-02 triangles with their old UVs) for the texture reference repair."""
import math
import os
import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- old-mesh reference (revision 02: body UV layout = material 0, head layout = material 1)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source_snapshot.blend'))
old = bpy.data.objects['Wyrm']; rig = bpy.data.objects['Wyrm_Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
me = old.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
np.savez(os.path.join(HERE, 'work', 'old_uv3d.npz'),
         uv=np.array([[uv[l].uv[:] for l in t.loops] for t in me.loop_triangles]),
         xyz=np.array([[me.vertices[v].co[:] for v in t.vertices] for t in me.loop_triangles]),
         mat=np.array([t.material_index for t in me.loop_triangles]))

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'uv_final.blend'))
mesh = bpy.data.objects['Wyrm']
bm = bmesh.new(); bm.from_mesh(mesh.data)
uvl = bm.loops.layers.uv.active
part = bm.verts.layers.int.get('part')
deform = bm.verts.layers.deform.active
head_group = mesh.vertex_groups['Head'].index

# ---- 2. eyes: measure, delete, rebuild
eyes = []
for pid in (5, 6):
    vs = [v for v in bm.verts if v[part] == pid]
    lo = Vector([min(v.co[k] for v in vs) for k in range(3)]); hi = Vector([max(v.co[k] for v in vs) for k in range(3)])
    eyes.append((pid, (lo + hi) / 2, (hi - lo) / 2))
    bmesh.ops.delete(bm, geom=vs, context='VERTS')
print('EYES', [(p, [round(c, 4) for c in ctr], [round(r, 4) for r in rad]) for p, ctr, rad in eyes])

# ---- 1. holes
loops = []
edges = {e for e in bm.edges if e.is_boundary}
while edges:
    e = edges.pop(); loop = [e]; fr = [e]
    while fr:
        x = fr.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in edges:
                    edges.remove(y); loop.append(y); fr.append(y)
    loops.append(loop)
filled = []
patch_layer = bm.faces.layers.int.new('patch')
hole_id = 0
for loop in loops:
    vs = {v for e in loop for v in e.verts}
    centre = sum((v.co for v in vs), Vector()) / len(vs)
    teeth = len(loop) == 5 and all(v[part] == 4 for v in vs)
    if teeth or len(loop) > 12:
        continue
    # order the loop's vertices
    start = loop[0].verts[0]; order = [start]; prev = None; cur = start
    while True:
        nxt = [e.other_vert(cur) for e in cur.link_edges if e in loop and e.other_vert(cur) is not prev]
        if not nxt or nxt[0] is start:
            break
        prev, cur = cur, nxt[0]; order.append(cur)
    if len(order) != len(vs):          # bowtie loops: fan around a centre vertex, wound with each rim face
        f0 = loop[0].link_faces[0]
        cv = bm.verts.new(centre)
        for g, w in loop[0].verts[0][deform].items():
            cv[deform][g] = w
        nf = []
        for e in loop:
            a, b = e.verts; ef = e.link_faces[0]; fv = list(ef.verts)
            if (fv.index(b) - fv.index(a)) % len(fv) == 1:
                a, b = b, a
            try:
                nf.append(bm.faces.new((a, b, cv)))
            except ValueError:
                pass
        for face in nf:
            face.material_index = f0.material_index; face.smooth = True
            for l in face.loops:
                src = next((ol for ol in l.vert.link_loops if ol.face not in nf
                            and ol.face.material_index == face.material_index), None)
                if src is not None:
                    l[uvl].uv = src[uvl].uv
        for face in nf:
            for l in face.loops:
                if l.vert is cv:
                    l[uvl].uv = face.loops[0][uvl].uv
        hole_id += 1
        for face in nf:
            face[patch_layer] = hole_id
        filled.append((len(loop), [round(c, 3) for c in centre], 'fan', len(nf)))
        continue
    # wind against the adjacent face so normals stay consistent
    e0 = loop[0]; f0 = e0.link_faces[0]
    a, b = e0.verts
    fv = list(f0.verts); ia, ib = fv.index(a), fv.index(b)
    adj_forward = (ib - ia) % len(fv) == 1          # adjacent face runs a -> b, the new face must run b -> a
    ia2, ib2 = order.index(a), order.index(b)
    if adj_forward == ((ib2 - ia2) % len(order) == 1):
        order.reverse()
    face = bm.faces.new(order)
    face.material_index = f0.material_index; face.smooth = True
    for l in face.loops:
        src = next((ol for ol in l.vert.link_loops if ol.face is not face and ol.face.material_index == face.material_index), None)
        if src is not None:
            l[uvl].uv = src[uvl].uv
    hole_id += 1
    face[patch_layer] = hole_id
    bmesh.ops.triangulate(bm, faces=[face])
    filled.append((len(loop), [round(c, 3) for c in centre]))
print('HOLES filled', filled)

def free_square(slot):
    N = 256
    cover = np.zeros((N, N), bool)
    for f in bm.faces:
        if f.material_index != slot:
            continue
        us = [l[uvl].uv for l in f.loops]
        x0 = int(max(0, min(u.x for u in us)) * N); x1 = int(min(1, max(u.x for u in us)) * N) + 1
        y0 = int(max(0, min(u.y for u in us)) * N); y1 = int(min(1, max(u.y for u in us)) * N) + 1
        cover[max(0, y0 - 1):y1 + 1, max(0, x0 - 1):x1 + 1] = True
    return cover


# ---- hole patches: own small cell each (planar projection), part 7; compose paints the revision-02 colour there
hole_faces = {}
for f in bm.faces:
    if f[patch_layer]:
        hole_faces.setdefault(f[patch_layer], []).append(f)
for k, faces in hole_faces.items():
    slot = faces[0].material_index
    cover = free_square(slot); N = cover.shape[0]
    sq = np.zeros((N + 1, N + 1), int)
    for i in range(N):
        for j in range(N):
            if not cover[i, j]:
                sq[i + 1, j + 1] = 1 + min(sq[i, j + 1], sq[i + 1, j], sq[i, j])
    i, j = np.unravel_index(np.argmax(sq), sq.shape); size = min(sq[i, j], 6)
    y0, x0 = (i - size) / N, (j - size) / N; cell = (size - 1) / N
    vs = {v for f in faces for v in f.verts}
    pts = np.array([v.co[:] for v in vs]); c = pts.mean(0); _, _, vt = np.linalg.svd(pts - c)
    a, b = vt[0], vt[1]
    pa = (pts - c) @ a; pb = (pts - c) @ b; ext = max(np.ptp(pa), np.ptp(pb), 1e-6)
    for f in faces:
        for l in f.loops:
            q = np.array(l.vert.co[:]) - c
            l[uvl].uv = (x0 + 1 / N + cell * ((q @ a - pa.min()) / ext), y0 + 1 / N + cell * ((q @ b - pb.min()) / ext))
    print('PATCH cell', k, 'material', slot, 'faces', len(faces), 'cell texels', size)

# ---- eyeballs: free square in the head layout
N = 256
cover = np.zeros((N, N), bool)
for f in bm.faces:
    if f.material_index != 1:
        continue
    us = [l[uvl].uv for l in f.loops]
    x0 = int(max(0, min(u.x for u in us)) * N); x1 = int(min(1, max(u.x for u in us)) * N) + 1
    y0 = int(max(0, min(u.y for u in us)) * N); y1 = int(min(1, max(u.y for u in us)) * N) + 1
    cover[y0:y1, x0:x1] = True
# largest empty square (dynamic programming), centre and half size in cells
sq = np.zeros((N + 1, N + 1), int)
for i in range(N):
    for j in range(N):
        if not cover[i, j]:
            sq[i + 1, j + 1] = 1 + min(sq[i, j + 1], sq[i + 1, j], sq[i, j])
i, j = np.unravel_index(np.argmax(sq), sq.shape); size = sq[i, j] - 1
half = size // 2; cy, cx = i - 1 - size // 2, j - 1 - size // 2
print('FREE square', half * 2, 'cells of', N, 'at', cx, cy)
SEG, RINGS = 16, 10
for k, (pid, ctr, rad) in enumerate(eyes):
    # each eye gets half of the free square (left/right)
    u0 = (cx - half + (half if k else 0)) / N; v0 = (cy - half) / N; du = half / N; dv = 2 * half / N
    grid = []
    for i in range(RINGS + 1):
        th = math.pi * i / RINGS
        row = []
        for j in range(SEG):
            ph = 2 * math.pi * j / SEG
            p = Vector((math.sin(th) * math.cos(ph) * rad.x * 1.1, math.sin(th) * math.sin(ph) * rad.y * 1.1,
                        math.cos(th) * rad.z * 1.1)) + ctr
            v = bm.verts.new(p); v[part] = pid; v[deform][head_group] = 1.0
            row.append(v)
        grid.append(row)
    for i in range(RINGS):
        for j in range(SEG):
            j2 = (j + 1) % SEG
            quad = [grid[i][j], grid[i][j2], grid[i + 1][j2], grid[i + 1][j]]
            if len({id(v) for v in quad}) < 4 and i not in (0, RINGS - 1):
                continue
            try:
                f = bm.faces.new(quad)
            except ValueError:
                continue
            f.material_index = 1; f.smooth = True
            for l in f.loops:   # flat side projection: the whole cell shows the visible iris
                q = l.vert.co - ctr
                l[uvl].uv = (u0 + du * (0.5 + 0.45 * q.y / (rad.y * 1.1)), v0 + dv * (0.5 + 0.45 * q.z / (rad.z * 1.1)))
bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v[part] in (5, 6)], dist=1e-7)

# ---- 3. UV overlaps (user review of revision 05): Smart UV packing left some faces sharing texels with faces
# elsewhere (hind-thigh triangles showing belly plates). Both faces of every overlapping pair move into their own
# free cells (tagged 'moved'); compose recolours them from their nearest correctly mapped 3D neighbours.
moved_layer = bm.faces.layers.int.new('moved')
bm.faces.ensure_lookup_table()


def raster_ids(slot, N=2048):
    owner = -np.ones((N, N), int); pairs = {}
    for f in bm.faces:
        if f.material_index != slot:
            continue
        us = [l[uvl].uv for l in f.loops]
        for k in range(1, len(us) - 1):
            p = np.array([[us[0].x, us[0].y], [us[k].x, us[k].y], [us[k + 1].x, us[k + 1].y]]) * N
            p[:, 1] = N - p[:, 1]
            x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
            x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N - 1), min(y1, N - 1)
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
            a, b, c = p; den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-12:
                continue
            w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
            w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
            ins = (w0 > .02) & (w1 > .02) & (1 - w0 - w1 > .02)
            ys, xs = np.nonzero(ins); ys += y0; xs += x0
            prev = owner[ys, xs]
            for o in set(prev[prev >= 0].tolist()):
                key = (o, f.index); pairs[key] = pairs.get(key, 0) + int((prev == o).sum())
            owner[ys, xs] = f.index
    return pairs


moved = set()
for slot in (0, 1):
    for (a_, b_), n_ in raster_ids(slot).items():
        if n_ >= 4 and (bm.faces[a_].calc_center_median() - bm.faces[b_].calc_center_median()).length > .01:
            moved.update((a_, b_))
for slot in (0, 1):
    faces = [bm.faces[i] for i in sorted(moved) if bm.faces[i].material_index == slot]
    if not faces:
        continue
    cover = free_square(slot); N = cover.shape[0]
    for CELL in (4, 3, 2):                     # 4 of 256 = 32 texels at 2K; smaller where the layout is crowded
        free = [(i, j) for i in range(1, N - CELL, CELL + 1) for j in range(1, N - CELL, CELL + 1)
                if not cover[i:i + CELL, j:j + CELL].any()]
        if len(free) >= len(faces):
            break
    assert len(free) >= len(faces), (len(free), len(faces))
    for f, (i, j) in zip(faces, free):
        pts = [l.vert.co for l in f.loops]
        e1 = (pts[1] - pts[0]); n_ = f.normal; e2 = n_.cross(e1)
        q = [((p - pts[0]).dot(e1.normalized()), (p - pts[0]).dot(e2.normalized())) for p in pts]
        qa = np.array(q); qa -= qa.min(0); qa /= max(qa.max(), 1e-9)
        for l, (u_, v_) in zip(f.loops, qa):
            l[uvl].uv = ((j + .5 + u_ * (CELL - 1)) / N, (i + .5 + v_ * (CELL - 1)) / N)
        f[moved_layer] = 1
    print('MOVED', len(faces), 'faces of material', slot, 'to free cells')
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if all(v[part] in (5, 6) for v in f.verts)])
bm.to_mesh(mesh.data); bm.free()
open_after = sum(1 for e in mesh.data.edges if False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv_final_v5.blend'))
print('PATCHED tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons))
