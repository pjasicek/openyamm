"""Fit each Smart Topology head (meshy/head<k>_smart_topology_v1, Meshy frame: snout toward -Y, up +Z) to our neck k.

Per head:
  - weld, keep the largest piece; the neck's end is its lowest slab (capped),
  - centreline: march slabs (as rig_hyd.py) from that loop's centre into the neck up to the head; snout tip = the
    vertex farthest along the final direction; arc s measured back from the tip; radius = median slab distance,
  - scale sigma: our neck radius profile (work/rig.json chain k, arc from its tip) against sigma x the new one over
    our s in FIT_RANGE (the neck just behind the skull); a 1-D search,
  - trims: the head and its neck up to KEEP_N (graft) and UPLOAD_N (retexture) model units from the tip,
  - clean UVs for the retexture: smart projection, islands at equal texel density, packed into 0..1.
Writes work/heads/h<k>_st.blend (object 'Head<k>' trimmed at KEEP_N for the graft, 'Head<k>_upload' trimmed at
UPLOAD_N with UVs; Meshy frame), work/heads/h<k>_fit.json (centreline, arc, radii,
tip, sigma) and texturing/head<k>_st_upload.glb (the Meshy retexture upload).
  blender --background --python scripts/head_fit.py -- [k ...]"""
import bpy, bmesh, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HEADS = [int(a) for a in args] or [1, 2, 3, 4, 5]
FIT_RANGE = (0.22, 0.45)          # our arc from the snout tip (m) where both necks are plain tubes
KEEP_N = 1.0                      # model units kept for the graft geometry (graft_heads.py cuts the stub shorter)
UPLOAD_N = 0.8                    # model units kept on the retexture upload (skull ~0.40 + the stub the graft keeps)
STEP, SLAB, REACH, MAX_TURN = 0.025, 0.018, 0.4, math.radians(25)
SKULL = 0.33                      # model units: neck trace stops this far from the snout tip
MIN_PIECE = 60                    # vertices: smaller loose pieces are Meshy specks
rig = json.load(open(os.path.join(HERE, 'work', 'rig.json')))
os.makedirs(os.path.join(HERE, 'work', 'heads'), exist_ok=True)
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)


def our_profile(k):
    """(arc from tip, radius) at our chain k's joints."""
    J = np.array(rig['chains'][k]['joints']); R = np.array(rig['chains'][k]['radius'])
    L = np.linalg.norm(np.diff(J, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(L[::-1])])[::-1]          # joint i: arc from the tip
    return s, R


def march(points, start, direction):
    p = np.array(start, float); d = np.array(direction, float); d /= np.linalg.norm(d)
    out, rad = [p.copy()], []
    for _ in range(400):
        q = p + STEP * d; rel = points - q
        s = points[(np.abs(rel @ d) < SLAB) & (np.linalg.norm(rel, axis=1) < REACH)]
        if len(s) < 8:
            break
        lo, hi = np.percentile(s, 8, axis=0), np.percentile(s, 92, axis=0)
        c = (lo + hi) / 2; c = c - ((c - q) @ d) * d
        nd = (c - p) / np.linalg.norm(c - p)
        ang = math.acos(max(-1.0, min(1.0, float(nd @ d))))
        if ang > MAX_TURN:
            axis = np.cross(d, nd); axis /= np.linalg.norm(axis)
            nd = d * math.cos(MAX_TURN) + np.cross(axis, d) * math.sin(MAX_TURN); c = p + STEP * nd
        if len(out) > 6 and np.linalg.norm(np.array(out[:-5]) - c, axis=1).min() < 0.6 * STEP:
            break                                   # turned back onto itself
        out.append(c.copy()); rad.append(float(np.median(np.linalg.norm(s - c, axis=1))))
        d, p = nd, c
    return np.array(out), np.array([rad[0]] + rad)


for k in HEADS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy', f'head{k}_smart_topology_v1', 'model_urls_glb.glb'))
    obj = next(o for o in bpy.data.objects if o.type == 'MESH')
    for o in list(bpy.data.objects):
        if o is not obj:
            bpy.data.objects.remove(o, do_unlink=True)
    obj.parent = None
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.verts.ensure_lookup_table()
    seen = set(); pieces = []
    for v in bm.verts:
        if v in seen:
            continue
        stack = [v]; seen.add(v); piece = []
        while stack:
            a = stack.pop(); piece.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b not in seen:
                    seen.add(b); stack.append(b)
        pieces.append(piece)
    pieces.sort(key=len)
    # fin membranes are separate pieces in the Meshy mesh: keep every sizeable piece
    bmesh.ops.delete(bm, geom=[v for p in pieces if len(p) < MIN_PIECE for v in p], context='VERTS')
    # neck end: the lowest slab (the Meshy neck runs down and ends in a capped cut; the longest open boundary is the
    # mouth)
    co = np.array([tuple(v.co) for v in bm.verts])
    low = co[co[:, 2] < co[:, 2].min() + 0.03]
    centre = (low.min(0) + low.max(0)) / 2; n = np.array([0, 0, 1.0])
    # snout tip: the most forward vertex (Meshy frame: snout toward -Y); the neck trace stops SKULL away from it and
    # the skull is the straight segment to the tip (a slab march loops inside the skull)
    tip = co[np.argmin(co[:, 1])]
    C, Rr = march(co, centre, n)
    stop = np.nonzero(np.linalg.norm(C - tip, axis=1) < SKULL)[0]
    if len(stop):
        C, Rr = C[:stop[0] + 1], Rr[:stop[0] + 1]
    for _ in range(20):                                # spines and belly rings make the slab centres wiggle
        C[1:-1] = 0.5 * C[1:-1] + 0.25 * (C[:-2] + C[2:])
    C = np.vstack([C, tip]); Rr = np.append(Rr, Rr[-1])
    L = np.linalg.norm(np.diff(C, axis=0), axis=1)
    s_new = np.concatenate([[0], np.cumsum(L[::-1])])[::-1]       # arc from the tip
    # scale: our radius at our arc s vs sigma * new radius at s / sigma
    s_old, R_old = our_profile(k)
    grid = np.linspace(*FIT_RANGE, 20)
    r_old = np.interp(grid, s_old[::-1], R_old[::-1])
    best = (1e9, 1.0)
    for sigma in np.linspace(0.05, 1.0, 400):
        r_new = sigma * np.interp(grid / sigma, s_new[::-1], Rr[::-1])
        err = float(((r_new - r_old) ** 2).mean())
        if err < best[0]:
            best = (err, sigma)
    sigma = best[1]
    vs = np.zeros(len(co)); vr = np.zeros(len(co)); rr = np.zeros(len(co))
    for i, p in enumerate(co):
        j = int(np.argmin(np.linalg.norm(C - p, axis=1))); vs[i] = s_new[j]; vr[i] = np.linalg.norm(C[j] - p); rr[i] = Rr[j]
    bm.to_mesh(obj.data); bm.free()
    obj.name = obj.data.name = f'Head{k}'
    for p in obj.data.polygons:
        p.use_smooth = True
    for layer in list(obj.data.uv_layers):
        obj.data.uv_layers.remove(layer)


    def trimmed(limit, name):
        """Copy of the head with the neck beyond arc `limit` (model units) removed: only vertices near the neck axis
        are judged, so fins and horns that sweep back beyond the cut stay attached; dorsal spines left loose behind the
        cut are dropped with the other loose bits."""
        me = obj.data.copy(); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
        b2 = bmesh.new(); b2.from_mesh(me); b2.verts.ensure_lookup_table()
        arc_l = b2.verts.layers.float.new('arc')
        for v in b2.verts:
            v[arc_l] = vs[v.index]
        bmesh.ops.delete(b2, geom=[b2.verts[i] for i in np.nonzero((vs > limit) & (vr < 2.2 * rr))[0]], context='VERTS')
        b2.verts.ensure_lookup_table(); seen = set(); pieces = []
        for v in b2.verts:
            if v in seen:
                continue
            stack = [v]; seen.add(v); piece = []
            while stack:
                a_ = stack.pop(); piece.append(a_)
                for e in a_.link_edges:
                    w = e.other_vert(a_)
                    if w not in seen:
                        seen.add(w); stack.append(w)
            pieces.append(piece)
        pieces.sort(key=len)
        # pieces cut off behind the trim (dorsal spines) go; fins (separate pieces near the skull) stay
        bmesh.ops.delete(b2, geom=[v for p_ in pieces[:-1] if len(p_) < MIN_PIECE
                                   or min(x[arc_l] for x in p_) > limit * 0.8 for v in p_],
                         context='VERTS')
        bmesh.ops.triangulate(b2, faces=b2.faces)
        b2.verts.layers.float.remove(arc_l)
        b2.to_mesh(me); b2.free()
        return o


    geo = trimmed(KEEP_N, f'Head{k}_geo')
    up = trimmed(UPLOAD_N, f'Head{k}_upload')
    bpy.data.objects.remove(obj, do_unlink=True)
    geo.name = geo.data.name = f'Head{k}'
    up.data.uv_layers.new(name='UVMap')
    for o in list(bpy.context.scene.objects):
        o.select_set(o == up)
    bpy.context.view_layer.objects.active = up
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0)
    bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(shape_method='CONCAVE', rotate=True, margin=0.003)
    bpy.ops.object.mode_set(mode='OBJECT')
    up.data.materials.clear(); up.data.materials.append(bpy.data.materials.new(f'Head{k}'))
    obj = geo
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    json.dump({'centreline': C.round(6).tolist(), 'arc': s_new.round(6).tolist(), 'radius': Rr.round(6).tolist(),
               'tip': tip.round(6).tolist(), 'sigma': sigma, 'fit_rmse': math.sqrt(best[0])},
              open(os.path.join(HERE, 'work', 'heads', f'h{k}_fit.json'), 'w'), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'heads', f'h{k}_st.blend'))
    for o in list(bpy.context.scene.objects):
        o.select_set(o == up)
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', f'head{k}_st_upload.glb'), use_selection=True,
                              export_format='GLB', export_yup=True, export_texcoords=True, export_normals=True,
                              export_materials='PLACEHOLDER')
    print(f'FIT head {k}: centreline {len(C)} pts, neck length {s_new[0]:.3f}, sigma {sigma:.4f} '
          f'(rmse {math.sqrt(best[0]) * 1000:.1f} mm), geometry triangles {tris}, upload triangles '
          f'{sum(len(p.vertices) - 2 for p in up.data.polygons)}')
