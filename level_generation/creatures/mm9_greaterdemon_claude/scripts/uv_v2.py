"""UVs v2 (2026-10-30 rework) and the three neutral retexture uploads.

v1 used Smart UV Project (66 deg) on the reduced Meshy body: about two thousand small islands, 17 % of the 2K atlas
covered (margins ate the rest), 141 texels/m on the body, and Meshy painted each island separately (the blotchy,
smeared shoulders). v2 unwraps with xatlas (scripts/xatlas_uv.py, larger charts, packed at the final resolution):
- 'UVMap': the body, wings and small pieces (head = 0 faces), one 2K atlas;
- 'HeadUV': the three heads (head_split_v2.py: 1 main, 2 left arm head, 3 right arm head) in one 1K head atlas at
  equal density. The right arm head is painted by baking the mirrored left one (bake_armhead.py), not by Meshy.
For the body upload the head faces need some UVs (they occlude the chest in the masters): their HeadUV layout is put
into the largest empty square of the body atlas; those texels are thrown away by compose_v2.py.

Args: <in blend> <out blend> <body upload> <head upload> <arm head upload> <report json>; env XATLAS_PYTHON."""
import bpy, bmesh, json, os, subprocess, sys
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UP_BODY, UP_HEAD, UP_ARM, REP = argv
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
PY = os.environ['XATLAS_PYTHON']
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
dup_fix = me.validate()          # the decimation leaves a few duplicate faces
bm = bmesh.new(); bm.from_mesh(me)
ntri = sum(1 for f in bm.faces if len(f.verts) > 3)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(me); bm.free()
for uv in list(me.uv_layers):
    me.uv_layers.remove(uv)
me.uv_layers.new(name='UVMap')
me.uv_layers.new(name='HeadUV')
head = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', head)
rep = {'triangulated_ngons': ntri, 'validate_fixed': bool(dup_fix), 'faces': len(me.polygons)}


PIECE = np.zeros(len(me.vertices), np.int32)
me.attributes['piece'].data.foreach_get('value', PIECE)
# relative texel density per part (each part is its own loose shell, scaled about its centroid before charting):
# spikes and teeth (piece 2) are plain ivory cones, the membrane (piece 3) a dark sheet with veins
DENSITY = {2: 0.55, 3: 0.8}


def scaled_coords():
    co = np.array([v.co[:] for v in me.vertices], np.float64)
    bmc = bmesh.new(); bmc.from_mesh(me); bmc.verts.ensure_lookup_table()
    comp = -np.ones(len(co), np.int64); k = 0
    for v in bmc.verts:
        if comp[v.index] >= 0:
            continue
        st = [v]; comp[v.index] = k
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if comp[y.index] < 0:
                    comp[y.index] = k; st.append(y)
        k += 1
    bmc.free()
    out = co.copy()
    for c in range(k):
        m = comp == c
        s = DENSITY.get(int(np.bincount(PIECE[m]).argmax()), 1.0)
        if s != 1.0:
            cen = co[m].mean(0)
            out[m] = cen + (co[m] - cen) * s
    return out.astype(np.float32)


CO_UV = scaled_coords()


def unwrap(faces, layer, res, tag, cost, padding):
    co = CO_UV
    tri = np.array([list(me.polygons[f].vertices) for f in faces], np.int64)
    used = np.unique(tri)
    remap = -np.ones(len(co), np.int64); remap[used] = np.arange(len(used))
    src = os.path.join(PROJ, 'work', f'xatlas_{tag}_in.npz'); dst = os.path.join(PROJ, 'work', f'xatlas_{tag}_out.npz')
    np.savez(src, co=co[used], tri=remap[tri])
    out = subprocess.run([PY, os.path.join(HERE, 'xatlas_uv.py'), src, dst, str(res), str(cost), str(padding)],
                         check=True, capture_output=True, text=True).stdout.strip()
    print(out)
    uv = np.load(dst)['uv']
    data = me.uv_layers[layer].data
    for f, corners in zip(faces, uv):
        p = me.polygons[f]
        for li, c in zip(p.loop_indices, corners):
            data[li].uv = (float(c[0]), float(c[1]))
    return out, uv


def coverage(uv, n):
    cov = np.zeros((n, n), bool)
    for t in uv * n:
        x0, y0 = np.floor(t.min(0)).astype(int); x1, y1 = np.ceil(t.max(0)).astype(int)
        gx, gy = np.meshgrid(np.arange(max(x0, 0), min(x1, n)) + 0.5, np.arange(max(y0, 0), min(y1, n)) + 0.5)
        a, b, c = t
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12 or gx.size == 0:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        ins = (l1 >= -0.02) & (l2 >= -0.02) & (1 - l1 - l2 >= -0.02)
        cov[gy[ins].astype(int), gx[ins].astype(int)] = True
    return cov


bf = [i for i in range(len(me.polygons)) if head[i] == 0]
hf = [i for i in range(len(me.polygons)) if head[i] > 0]
rep['body_xatlas'], buv = unwrap(bf, 'UVMap', 2048, 'body', 3.5, 4)
rep['head_xatlas'], huv = unwrap(hf, 'HeadUV', 1024, 'head', 3.0, 3)
bc = coverage(buv, 512)
hc = coverage(huv, 512)
rep['body_coverage'] = round(float(bc.mean()), 3)
rep['head_coverage'] = round(float(hc.mean()), 3)
# largest empty square in the body atlas (2 px clearance at 512) for the head faces of the body upload
grown = bc.copy()
for dy in range(-2, 3):
    for dx in range(-2, 3):
        grown |= np.roll(np.roll(bc, dy, 0), dx, 1)
free = ~grown
dp = np.zeros(free.shape, np.int32)
for y in range(free.shape[0]):
    for x in range(free.shape[1]):
        if free[y, x]:
            dp[y, x] = 1 + (min(dp[y - 1, x], dp[y, x - 1], dp[y - 1, x - 1]) if x and y else 0)
y, x = np.unravel_index(np.argmax(dp), dp.shape)
side = dp[y, x] / 512
sq = (float((x + 1) / 512 - side), float((y + 1) / 512 - side), float(side))
rep['head_square_in_body_atlas'] = [round(v, 4) for v in sq]
bdata, hdata = me.uv_layers['UVMap'].data, me.uv_layers['HeadUV'].data
for f in hf:
    for li in me.polygons[f].loop_indices:
        u, v = hdata[li].uv
        bdata[li].uv = (sq[0] + u * sq[2], sq[1] + v * sq[2])
me.uv_layers.active = me.uv_layers['UVMap']
# texel density report (texels per metre at the final sizes)
co = np.array([v.co[:] for v in me.vertices])


def density(faces, layer, size):
    d = me.uv_layers[layer].data
    a3 = np.array([me.polygons[f].area for f in faces])
    au = []
    for f in faces:
        U = np.array([d[li].uv[:] for li in me.polygons[f].loop_indices])
        au.append(0.5 * abs((U[1, 0] - U[0, 0]) * (U[2, 1] - U[0, 1]) - (U[2, 0] - U[0, 0]) * (U[1, 1] - U[0, 1])))
    au = np.array(au)
    return round(float(np.sqrt(au.sum() / a3.sum()) * size), 1)


pf = np.array([PIECE[list(p.vertices)].max() for p in me.polygons])
rep['texels_per_m'] = {'body_2k': density([f for f in bf if pf[f] in (0, 4)], 'UVMap', 2048),
                       'spikes_2k': density([f for f in bf if pf[f] == 2], 'UVMap', 2048),
                       'membrane_2k': density([f for f in bf if pf[f] == 3], 'UVMap', 2048),
                       'heads_1k': density(hf, 'HeadUV', 1024)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)


def upload(path, faces_keep, layer):
    dup = body.copy(); dup.data = body.data.copy(); dup.modifiers.clear(); dup.parent = None
    dup.matrix_world = body.matrix_world
    bpy.context.scene.collection.objects.link(dup)
    d = dup.data
    if faces_keep is not None:
        b2 = bmesh.new(); b2.from_mesh(d); b2.faces.ensure_lookup_table()
        keep = set(faces_keep)
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index not in keep], context='FACES')
        bmesh.ops.delete(b2, geom=[v for v in b2.verts if not v.link_faces], context='VERTS')
        b2.to_mesh(d); b2.free()
    for l in [l.name for l in d.uv_layers if l.name != layer]:
        d.uv_layers.remove(d.uv_layers[l])
    dup.vertex_groups.clear()
    d.materials.clear()
    for o in bpy.data.objects:
        o.select_set(o == dup)
    bpy.context.view_layer.objects.active = dup
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                              export_skins=False, export_animations=False, export_materials='NONE',
                              export_attributes=False, export_morph=False)
    n = len(d.polygons)
    bpy.data.objects.remove(dup, do_unlink=True)
    return n


rep['upload_faces'] = {'body': upload(UP_BODY, None, 'UVMap'),
                       'head': upload(UP_HEAD, [i for i in hf if head[i] == 1], 'HeadUV'),
                       'armhead': upload(UP_ARM, [i for i in hf if head[i] == 2], 'HeadUV')}
json.dump(rep, open(REP, 'w'), indent=1)
print('UVV2', json.dumps(rep))
