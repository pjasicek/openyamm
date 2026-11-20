"""Prepare each Smart Topology head (meshy/head<k>_smart_topology_v1; Meshy frame: unit box, snout toward -Y, neck down
to z -0.5) for the graft AND the retexture, as one mesh (after mm6_hyd_claude/scripts/head_fit.py, which cut and
decimated in the graft and baked the texture from a separately retextured copy; here the grafted mesh is the uploaded
mesh, so its retexture maps apply directly through its own UVs):
  - weld, drop specks (< MIN_PIECE vertices; teeth and horn pieces stay),
  - cut behind the skull: a plane through the throat and the nape (PLANES, read off side_plot.py views of each head)
    across the main skin piece (an automatic centreline cut wandered into the spiky manes; a horizontal cut below the
    jaw kept each head's arched nape, 0.5 m of neck that did not follow ours); loose pieces
    (horns, crest spikes, fins, teeth) stay whole when their centroid is on the head side; severed remnants of the
    main piece behind it go; small open loops other than the cut ring (the largest loop on the plane) are capped,
  - decimation per piece (see the code), smooth shading,
  - UVs: smart projection at 66 degrees, islands at equal texel density, packed with MARGIN.
Writes work/heads/h<k>_st.blend (object 'Head<k>'), work/heads/h<k>_fit.json (centreline, arc, radius, tip, cut point and
normal) and texturing/head<k>_upload.glb. Args: -- [k ...]"""
import bpy, bmesh, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HEADS = [int(a) for a in args] or [1, 2, 3, 4, 5]
# cut planes per head: (throat y, z), (nape y, z) in the Meshy frame, read from side_plot.py views
PLANES = {1: ((0.06, -0.25), (0.24, 0.10)), 2: ((-0.02, 0.0), (0.12, 0.25)), 3: ((0.02, -0.02), (0.17, 0.22)),
          4: ((-0.05, 0.0), (0.02, 0.24)), 5: ((-0.047, -0.035), (0.04, 0.25))}

CUT_AXIS = 1.7
SKULL = 0.30
MIN_PIECE = 12
SMALL_PIECE = 150
MIN_EXTENT = 0.025
RATIO_SMALL, MIN_TRIS = 0.3, 14
RATIO_BIG = {1: 0.17, 2: 0.25, 3: 0.35, 4: 0.35, 5: 0.25}
MARGIN = 0.008
STEP, SLAB, REACH, MAX_TURN = 0.02, 0.016, 0.35, math.radians(25)
os.makedirs(os.path.join(HERE, 'work', 'heads'), exist_ok=True)
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)


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
            break
        out.append(c.copy()); rad.append(float(np.median(np.linalg.norm(s - c, axis=1))))
        d, p = nd, c
    return np.array(out), np.array([rad[0]] + rad)


def components(bm_):
    seen = set(); out = []
    for v in bm_.verts:
        if v in seen:
            continue
        stack = [v]; seen.add(v); piece = []
        while stack:
            a = stack.pop(); piece.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b not in seen:
                    seen.add(b); stack.append(b)
        out.append(piece)
    return out


def local(C, s_arc, p):
    """(arc, distance from the axis) of p at its nearest centreline segment."""
    best = (1e9, 0, 0.0)
    for i in range(len(C) - 1):
        a, b = C[i], C[i + 1]; d = b - a
        t = float(np.clip((p - a) @ d / (d @ d), 0, 1)); dist = float(np.linalg.norm(p - (a + t * d)))
        if dist < best[0]:
            best = (dist, i, t)
    dist, i, t = best
    return s_arc[i] + t * (s_arc[i + 1] - s_arc[i]), dist


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
    # decimate before the cut (so the cut ring stays an exact planar loop; decimating after it collapsed head 1's
    # ring to 9 vertices), piece by piece: the main shells by RATIO_BIG, small pieces (teeth, eyes, horn and crest tips)
    # by RATIO_SMALL with a floor of MIN_TRIS (one collapse over the whole head erased the teeth); specks under
    # MIN_EXTENT model units (under 2 cm in game) go
    pre_total = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    b0 = bmesh.new(); b0.from_mesh(obj.data); bmesh.ops.remove_doubles(b0, verts=b0.verts, dist=1e-6)
    for p in components(b0):
        P = np.array([tuple(v.co) for v in p])
        if len(p) < MIN_PIECE or np.linalg.norm(P.max(0) - P.min(0)) < MIN_EXTENT:
            bmesh.ops.delete(b0, geom=p, context='VERTS')
    b0.to_mesh(obj.data); b0.free(); obj.data.update()
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    parts = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in parts:
        n_t = sum(len(p.vertices) - 2 for p in o.data.polygons)
        r = RATIO_BIG[k] if len(o.data.vertices) > SMALL_PIECE else max(RATIO_SMALL, MIN_TRIS / max(n_t, 1))
        if r < 1.0:
            m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = r
            with bpy.context.temp_override(object=o, active_object=o):
                bpy.ops.object.modifier_apply(modifier=m.name)
    for o in bpy.data.objects:
        o.select_set(o in parts)
    obj = max(parts, key=lambda o: len(o.data.vertices)); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.delete(bm, geom=[v for p in components(bm) if len(p) < MIN_PIECE for v in p], context='VERTS')
    co = np.array([tuple(v.co) for v in bm.verts])
    tip = co[np.argmin(co[:, 1])]
    (ty, tz), (ny, nz) = PLANES[k]
    p0 = np.array([0.0, ty, tz]); line = np.array([0.0, ny - ty, nz - tz]); line /= np.linalg.norm(line)
    n = np.array([0.0, -line[2], line[1]])                    # in the yz plane, perpendicular to throat-nape
    if (tip - p0) @ n < 0:
        n = -n                                                  # toward the snout
    zc = -9.0
    pieces = components(bm); main = max(pieces, key=len); mset = set(main)
    side = lambda p: (np.asarray(p) - p0) @ n
    # loose pieces (horns, crest spikes, teeth, fins): kept whole when their centroid is on the head side
    loose_kept = set()
    for piece in pieces:
        if piece is main:
            continue
        if side(np.mean([np.array(v.co) for v in piece], 0)) < 0:
            bmesh.ops.delete(bm, geom=piece, context='VERTS')
        else:
            loose_kept |= set(piece)
    geom = list({e for v in main for e in v.link_edges}) + list({f for v in main for f in v.link_faces}) + main
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=p0.tolist(), plane_no=n.tolist())
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v not in loose_kept and side(v.co) < -1e-6], context='VERTS')
    # the skull is the component holding the snout; other main-piece remnants (a severed mane strip) go if behind
    comps = components(bm)
    tipv = min(bm.verts, key=lambda v: (np.array(v.co) - tip) @ (np.array(v.co) - tip))
    for piece in comps:
        if tipv not in piece and (np.mean([np.array(v.co) for v in piece], 0)[2] < zc + 0.05 or
                                  (side(np.mean([np.array(v.co) for v in piece], 0)) < 0.02 and len(piece) > 200)):
            bmesh.ops.delete(bm, geom=piece, context='VERTS')
    pc = p0; Tc = n; rc = 0.0                                  # Tc: cut normal toward the snout
    C = np.array([p0, tip]); R = np.array([0.1, 0.1]); s_arc = np.array([np.linalg.norm(tip - p0), 0.0])
    # cap open loops other than the cut ring (spine stumps)
    left = {e for e in bm.edges if e.is_boundary}; loops = []
    while left:
        e = left.pop(); comp = {e}; stack = [e]
        while stack:
            a = stack.pop()
            for v in a.verts:
                for f in v.link_edges:
                    if f in left:
                        left.discard(f); comp.add(f); stack.append(f)
        loops.append(comp)
    def planar(l):
        return float(np.abs([(np.array(v.co) - pc) @ Tc for e in l for v in e.verts]).mean())

    def extent(l):
        P = np.array([np.array(v.co) for e in l for v in e.verts]); return float(np.linalg.norm(P.max(0) - P.min(0)))
    ring = max([l for l in loops if planar(l) < 0.004] or loops, key=extent)
    if os.environ.get('LOOPDBG'):
        print('LOOPS', k, sorted([(len(l), round(planar(l), 4), round(extent(l), 3)) for l in loops], key=lambda x: -x[2])[:6])
    rc = 0.5 * extent(ring)
    ring_centre = np.mean([np.array(v.co) for e in ring for v in e.verts], 0)
    capped = 0
    for l in loops:
        if l is not ring and len(l) < 0.5 * len(ring):
            bmesh.ops.holes_fill(bm, edges=list(l), sides=0); capped += 1
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    total = pre_total
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
    for p in obj.data.polygons:
        p.use_smooth = True
    for layer in list(obj.data.uv_layers):
        obj.data.uv_layers.remove(layer)
    obj.data.uv_layers.new(name='UVMap')
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, area_weight=0.0)
    bpy.ops.uv.select_all(action='SELECT'); bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(shape_method='CONCAVE', rotate=True, margin=MARGIN)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.materials.clear(); obj.data.materials.append(bpy.data.materials.new(f'Head{k}'))
    obj.name = obj.data.name = f'Head{k}'
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    json.dump({'centreline': C.round(6).tolist(), 'arc': s_arc.round(6).tolist(), 'radius': R.round(6).tolist(),
               'tip': tip.round(6).tolist(), 'cut': {'point': pc.round(6).tolist(), 'normal': Tc.round(6).tolist(),
                                                    'ring_centre': ring_centre.round(6).tolist()}},
              open(os.path.join(HERE, 'work', 'heads', f'h{k}_fit.json'), 'w'), indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'heads', f'h{k}_st.blend'))
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', f'head{k}_upload.glb'), use_selection=True,
                              export_format='GLB', export_yup=True, export_texcoords=True, export_normals=True,
                              export_materials='PLACEHOLDER')
    print(f'PREP head {k}: centreline {len(C)} pts, neck arc {s_arc[0]:.3f}, cut ring radius {rc:.3f}, capped {capped}, '
          f'triangles {total} -> {tris}')
