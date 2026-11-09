"""Graft the head-only Meshy model (meshy/head_v1, from the Codex HD head turnaround) onto the Smart Topology parts
BEFORE rigging (after mm6_wdm_claude/scripts/graft_head.py, which grafted after rigging), so the joints, the weights
and the reduction treat it as one more part. Run on work/st_v0_parts.blend (examine_parts output); saves
work/st_v1_parts.blend (parts renumbered P00.., the head last) and work/graft.json (old -> new part numbers).

The head GLB is normalised first (unit height, centred in x/y, its invented bust's bottom at z 0). Parameters,
graft.json at the project root:
  cut_z       head faces wholly below this normalised height are deleted (Meshy's bust and shoulders); the
              neck above it is kept to sink into the body's neck
  braid       optional {"value_min": a, "value_max": b}: faces below cut_z whose base colour value lies between a
              (darker is the black bust cloth) and b (lighter is skin), hair colour, and
              that connect to the head through such faces are kept: the braid down the back. Each braid vertex
              keeps its height above the deleted bust surface and is re-seated that high above the body
  eye_z       normalised height of the new head's eyes; old_eyes: old eye parts. The head is scaled by `scale` and
              moved so its eye line lands on the old eye centre and its nose tip on the old face's foremost point,
              then `nudge` [x, y, z] (m) and `pitch` (deg about X through the eye line, + tips the face up)
  remove      old parts deleted whole (old hair, eyes, mouth bits, fragments)
  cut         {"piece": p, "overlap": m, "taper": m}: the fused old head part is bisected `overlap` above the new
              head's neck bottom and its neck tapers onto the new neck ring over `taper` below the cut
  hidden_in   {part: shell | {"shell": s, "above_z": z}}: faces of that old part lying wholly inside the closed shell
              part (above z) are deleted, and small leftover islands with them (the neck's chest inside the closed
              tunic poked out at the collar; the trousers' waist under the tunic poked out below the belt)
  fill_holes  {part: n}: boundary loops of at most n edges in that old part are filled (pinholes)
  source      parts blend to start from (default st_v0_parts.blend; pf4: st_v0_fixed_parts.blend from body_fix.py)
  shrink      extra uniform scale of the placed head about its neck cut (pf4 0.9: the first head read too big)
  weld        (with pitch 0: a pitched head's cut is no longer level) the old neck is cut exactly at the new neck's cut plane and tapered onto its ring without inset, the
              head's neck band is not pulled in: weld_neck.py then merges the two rims into one seam
  neck_extend {"to_z": z, "shell": p, "steps": n, "taper": f, "tuck_below": zt}: the head's neck rim is extruded down
              to z in n rings (narrowing by f per ring); rings below zt are kept 3 mm under the shell part (pm3: the
              tunic; tucking the ring above the collar left a ledge), so the join with the
              body is inside the clothing; the cut part is then bisected at z + overlap, without taper
  collar      {"piece": p, "above_z": z, "y_min": y, "factor": f}: that part's vertices above z behind y_min are
              pressed down towards z by f (fading in over 3 cm), so a high back collar frees the neck
  head_tris   decimation target of the head (it keeps its own UV layer 'HeadUV' and material 'HeadMeshy'); faces of
              skin colour (value > 0.6, saturation < 0.55, both head textures) are not decimated; and with
              protect_below_eye (m) nothing below that height over the eyes (pm3: Meshy painted its bust's dark
              shirt up the throat, and the collapse turned the throat into a ridge; tanned skin reads as hair)
Then every other body face inside the new head is deleted, rim vertices within `near` of the head are pulled just
inside it, and the head's lowest `band` (its neck cut) is pulled just under the body surface so neither edge shows.
Args: -- [tag]  with a tag: review/graft_<tag>_*.png (clay, the head orange) and review/fit_<tag>_*.png (old head
pieces and the placed new head rendered separately and blended, before anything is cut)"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

HERE = common.PROJECT
P = json.load(open(os.path.join(HERE, 'graft.json')))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
TAG = args[0] if args else None
INSET = 0.0015
NEAR = float(P.get('near', 0.03))
BAND = float(P.get('band', 0.03))
WELD = bool(P.get('weld'))

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, P.get('source', 'st_v0_parts.blend')))
parts = {int(o.name[1:]): o for o in bpy.data.objects if o.type == 'MESH' and o.name[0] == 'P'}


def part_co(i):
    return np.array([tuple(v.co) for v in parts[i].data.vertices])


# ---- old head landmarks -----------------------------------------------------------------------------------------
eye_old = np.mean([part_co(i).mean(0) for i in P['old_eyes']], axis=0)
old_head = [i for i in P.get('remove', []) if i not in P['old_eyes']]
pool = [part_co(i) for i in old_head]
if P.get('cut'):
    c = part_co(P['cut']['piece']); pool.append(c[c[:, 2] > eye_old[2] - 0.1])
pool = np.concatenate(pool)
face = pool[(np.abs(pool[:, 0] - eye_old[0]) < 0.02) & (pool[:, 2] < eye_old[2]) & (pool[:, 2] > eye_old[2] - 0.06)]
nose_old_y = float(face[:, 1].min())

# ---- new head: import, normalise, cut the bust -------------------------------------------------------------------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, P.get('head_glb', 'meshy/head_v1/model_urls_glb.glb')))
new = set(bpy.data.objects) - before
head = max((o for o in new if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
for o in new:
    if o is not head:
        bpy.data.objects.remove(o, do_unlink=True)
head.parent = None
for o in bpy.context.view_layer.objects:
    o.select_set(o is head)
bpy.context.view_layer.objects.active = head
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mat = head.data.materials[0]
img = next(n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image
           and any(l.to_socket.name == 'Base Color' for o in n.outputs for l in o.links))
iw, ih = img.size
px = np.array(img.pixels[:], np.float32).reshape(ih, iw, img.channels)
bm = bmesh.new(); bm.from_mesh(head.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
hc = np.array([tuple(v.co) for v in bm.verts]); lo, hi = hc.min(0), hc.max(0)
NORM = Matrix.Scale(1.0 / (hi[2] - lo[2]), 4) @ Matrix.Translation(Vector((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))
bm.transform(NORM)
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
uvl = bm.loops.layers.uv.active
CUT = P['cut_z']
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, CUT), plane_no=(0, 0, 1))
bm.faces.ensure_lookup_table()


def texel(f):
    u = np.mean([l[uvl].uv.x for l in f.loops]) % 1.0; v = np.mean([l[uvl].uv.y for l in f.loops]) % 1.0
    return px[min(int(v * ih), ih - 1), min(int(u * iw), iw - 1), :3]


low = {f for f in bm.faces if f.calc_center_median().z < CUT}
keep_low = set()
if P.get('braid'):
    def value(f):
        return float(texel(f).max())
    hairy = {f for f in low if P['braid'].get('value_min', 0.0) < value(f) < P['braid']['value_max']}
    front = [f for f in hairy if any(g not in low for e in f.edges for g in e.link_faces)]
    while front:                                     # grow from the faces touching the kept head
        f = front.pop()
        if f in keep_low:
            continue
        keep_low.add(f)
        front += [g for e in f.edges for g in e.link_faces if g in hairy and g not in keep_low]
doomed = low - keep_low
bust = bmesh.new()                                   # the deleted bust, to measure the braid's height above it
vmap = {}
for f in doomed:
    for v in f.verts:
        if v not in vmap:
            vmap[v] = bust.verts.new(v.co)
    try:
        bust.faces.new([vmap[v] for v in f.verts])
    except ValueError:
        pass
bmesh.ops.delete(bm, geom=list(doomed), context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.verts.index_update()
print('HEAD cut at', CUT, 'bust faces deleted', len(doomed), 'braid faces kept below the cut', len(keep_low))
# placement: scale, eye line onto the old eyes, nose tip onto the old face front, pitch about the eye line
S = P['scale']
hc = np.array([tuple(v.co) for v in bm.verts])
fb = hc[(np.abs(hc[:, 0]) < 0.05) & (hc[:, 2] < P['eye_z']) & (hc[:, 2] > P['eye_z'] - 0.06 / S)]
nose_new_y = float(fb[:, 1].min())
pivot_new = Vector((0.0, nose_new_y, P['eye_z']))
target = Vector((eye_old[0], nose_old_y, eye_old[2])) + Vector(P.get('nudge', [0, 0, 0]))
M = (Matrix.Translation(target) @ Matrix.Rotation(math.radians(-P.get('pitch', 0.0)), 4, 'X') @ Matrix.Scale(S, 4)
     @ Matrix.Translation(-pivot_new))
bm.transform(M); bust.transform(M)
Z_CUT = (M @ Vector((0.0, nose_new_y, CUT))).z
if P.get('shrink'):                                    # a smaller head about its neck cut (the neck stays where it is)
    ring_y = float(np.mean([v.co.y for v in bm.verts if abs(v.co.z - Z_CUT) < 0.004]))
    piv = Vector((target.x, ring_y, Z_CUT))
    K = Matrix.Translation(piv) @ Matrix.Scale(P['shrink'], 4) @ Matrix.Translation(-piv)
    bm.transform(K); bust.transform(K); M = K @ M
HEAD_MATRIX = M @ NORM                                  # Meshy's head GLB (transforms applied) -> body frame
braid_v = {v for f in keep_low if f.is_valid for v in f.verts}
bust_bvh = BVHTree.FromBMesh(bust) if len(bust.faces) else None
lift = {}
if bust_bvh and braid_v:
    for v in braid_v:
        loc, nrm, _, d = bust_bvh.find_nearest(v.co)
        if loc is not None:
            lift[v.index] = max(0.0, (v.co - loc).dot(nrm))
# skin faces (bright, warm, moderately saturated base colour) are spared by the decimation: Meshy's remesh gives the face few triangles and
# the hair cards most of them, so a uniform collapse flattened the face
skin_v = set()
for f in bm.faces:
    r, g, b = texel(f)
    if r > 0.6 and (r - b) / r < 0.55 and r >= g >= b:   # value > 0.6, saturation < 0.55
        skin_v |= {v.index for v in f.verts}
if 'protect_below_eye' in P:                          # everything under the brow line (placed: the old eye height)
    zmax = target.z + P['protect_below_eye']
    skin_v |= {v.index for v in bm.verts if v.co.z < zmax}
bm.to_mesh(head.data); bm.free(); bust.free()
head.data.uv_layers.active.name = 'HeadUV'
while len(head.data.uv_layers) > 1:
    head.data.uv_layers.remove(next(l for l in head.data.uv_layers if not l.active))
for p in head.data.polygons:
    p.use_smooth = True
mat.name = 'HeadMeshy'
head.data.materials.clear(); head.data.materials.append(mat)
hco0 = np.array([tuple(v.co) for v in head.data.vertices])
print('FIT eye_old', np.round(eye_old, 4).tolist(), 'nose_old_y', round(nose_old_y, 4), 'head height m',
      round(float(hco0[:, 2].max() - hco0[:, 2].min()), 4), 'crown z', round(float(hco0[:, 2].max()), 4),
      'old crown z', round(float(pool[:, 2].max()), 4))

if TAG:                                              # fit check before anything is cut
    scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
    om = bpy.data.materials.new('FitOld'); om.diffuse_color = (0.3, 0.5, 0.95, 1)
    nm = bpy.data.materials.new('FitNew'); nm.diffuse_color = (0.95, 0.55, 0.2, 1)
    keep_mats = {}
    for i, o in parts.items():
        keep_mats[i] = list(o.data.materials)
        o.data.materials.clear(); o.data.materials.append(om)
    head.data.materials[0] = nm
    shown = set(old_head) | set(P['old_eyes']) | ({P['cut']['piece']} if P.get('cut') else set())
    for which in ('old', 'new'):
        for i, o in parts.items():
            o.hide_render = which == 'new' or i not in shown
        head.hide_render = which == 'old'
        common.render_views(os.path.join(common.REVIEW, f'fit_{TAG}_{which}'), eye_old[2] - 0.05, 0.42,
                            views=('front', 'left'), resolution=(600, 600))
    for i, o in parts.items():
        o.hide_render = False
        o.data.materials.clear()
        for m in keep_mats[i]:
            o.data.materials.append(m)
    head.hide_render = False; head.data.materials[0] = mat

tris0 = sum(len(p.vertices) - 2 for p in head.data.polygons)
if P.get('head_tris') and tris0 > P['head_tris']:
    vg = head.vertex_groups.new(name='braid')
    vg.add(list(lift), 1.0, 'REPLACE')
    dg_ = head.vertex_groups.new(name='decimate')         # collapse only where weighted: everything but the skin
    dg_.add([v.index for v in head.data.vertices if v.index not in skin_v], 1.0, 'REPLACE')
    dec = head.modifiers.new('decimate', 'DECIMATE'); dec.ratio = P['head_tris'] / tris0
    dec.vertex_group = 'decimate'
    bpy.ops.object.modifier_apply(modifier=dec.name)
    # the braid lift survives decimation through the vertex group (weight 1 on braid vertices) and a nearest lookup
    old_lift = [(Vector(hco0[i]), d) for i, d in lift.items()]
    if old_lift:
        from mathutils.kdtree import KDTree
        kd = KDTree(len(old_lift))
        for k, (c, _) in enumerate(old_lift):
            kd.insert(c, k)
        kd.balance()
        gi = head.vertex_groups['braid'].index
        lift = {}
        for v in head.data.vertices:
            if any(g.group == gi and g.weight > 0.5 for g in v.groups):
                lift[v.index] = old_lift[kd.find(v.co)[1]][1]
    head.vertex_groups.remove(head.vertex_groups['braid']); head.vertex_groups.remove(head.vertex_groups['decimate'])
print('HEAD triangles', tris0, '->', sum(len(p.vertices) - 2 for p in head.data.polygons), 'braid verts', len(lift),
      'skin verts spared', len(skin_v))
EXT = P.get('neck_extend')                             # pm3: the head's own neck runs down inside the tunic
if EXT:
    eb = bmesh.new(); eb.from_mesh(head.data)
    for f in eb.faces:
        f.tag = False
    rim = [e for e in eb.edges if e.is_boundary and all(abs(v.co.z - Z_CUT) < 0.0015 for v in e.verts)]
    rim_v = {v for e in rim for v in e.verts}
    axis = Vector((float(np.mean([v.co.x for v in rim_v])), float(np.mean([v.co.y for v in rim_v])), 0.0))
    shell = BVHTree.FromObject(parts[EXT['shell']], bpy.context.evaluated_depsgraph_get(), deform=False)
    steps = EXT.get('steps', 3); drop = (Z_CUT - EXT['to_z']) / steps; edges = rim; inside_moved = 0
    for k in range(steps):
        res = bmesh.ops.extrude_edge_only(eb, edges=edges)
        for g in res['geom']:
            if isinstance(g, bmesh.types.BMFace):
                g.tag = True
        nv = [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]
        for v in nv:
            r = Vector((v.co.x - axis.x, v.co.y - axis.y, 0.0))
            v.co = Vector((axis.x, axis.y, 0.0)) + r * EXT.get('taper', 0.985) + Vector((0, 0, v.co.z - drop))
            loc, nrm, _, d = shell.find_nearest(v.co)
            if v.co.z > EXT.get('tuck_below', 10.0):   # the visible neck above the collar is left round
                continue
            if loc is not None and d < 0.03 and (v.co - loc).dot(nrm) > -0.003:   # keep it under the tunic
                v.co = loc - nrm * 0.003; inside_moved += 1
        edges = [g for g in res['geom'] if isinstance(g, bmesh.types.BMEdge) and g.is_boundary]
    # the extruded faces repeat the rim's UVs, which sit on island edges (one sampled a black gutter): every new
    # corner takes one UV in an unused part of the head layout (Meshy's cut-away bust left plenty), which
    # compose_peasant.py paints with the flat neck skin (work/graft.json neck_uv)
    uvl = eb.loops.layers.uv.active
    GR = 128
    occ = np.zeros((GR, GR), bool)
    for f in eb.faces:
        if f.tag:
            continue
        uv = np.array([tuple(l[uvl].uv) for l in f.loops]) % 1.0
        x0, y0 = np.floor(uv.min(0) * GR).astype(int); x1, y1 = np.floor(uv.max(0) * GR).astype(int)
        occ[max(y0, 0):min(y1, GR - 1) + 1, max(x0, 0):min(x1, GR - 1) + 1] = True
    free = [(gx, gy) for gy in range(4, GR - 4) for gx in range(4, GR - 4) if not occ[gy - 4:gy + 5, gx - 4:gx + 5].any()]
    gx, gy = free[0]
    NECK_UV = ((gx + 0.5) / GR, (gy + 0.5) / GR)
    for f in eb.faces:
        if f.tag:
            for l in f.loops:
                l[uvl].uv = NECK_UV
    for f in eb.faces:
        f.smooth = True
    eb.to_mesh(head.data); eb.free()
    print('HEAD neck extended from z', round(Z_CUT, 4), 'to', EXT['to_z'], 'rim verts', len(rim_v),
          'verts kept under the shell', inside_moved)
    Z_SEAM = Z_CUT                                      # where the head's own skin ends (compose fades from here)
    Z_CUT = EXT['to_z']
hbm = bmesh.new(); hbm.from_mesh(head.data); hbm.faces.ensure_lookup_table()
head_bvh = BVHTree.FromBMesh(hbm)
hco = np.array([tuple(v.co) for v in head.data.vertices]); hlo, hhi = hco.min(0), hco.max(0)


def inside_head(p):
    loc, nrm, _, _ = head_bvh.find_nearest(p)
    return (p - loc).dot(nrm) < 0, loc, nrm


# ---- old head pieces ------------------------------------------------------------------------------------------------
# The fused old head is bisected by a level plane `overlap` above the new head's neck bottom (a clean ring, no faces
# left hanging); the remaining neck below it tapers radially onto the new neck ring over `taper`, so the body neck
# meets the head's neck at the cut without a step or a lip. Faces of other parts inside the head are deleted.
for i in P.get('remove', []):
    bpy.data.objects.remove(parts.pop(i), do_unlink=True)
cut = P.get('cut')
neck = np.array([i not in lift for i in range(len(hco))])
z0 = Z_CUT                                           # the head's neck bottom: its cut plane (not a lone low vertex)
deleted = 0
if cut:
    zc = z0 + (0.0 if WELD else cut.get('overlap', 0.02))
    TAPER = cut.get('taper', 0.03)                      # 0: no taper (pm3: the old neck only stays below the collar)
    if WELD:                                          # the head's own rim on the cut plane (not the braid beside it)
        ring = np.array([tuple(v.co) for e in hbm.edges if e.is_boundary for v in e.verts if abs(v.co.z - z0) < 0.0015])
    else:
        ring = hco[neck & (hco[:, 2] > z0 - 0.006) & (hco[:, 2] < z0 + 0.012)]
    axis = np.median(ring[:, :2], axis=0)
    ring = ring[np.linalg.norm(ring[:, :2] - axis, axis=1) < 0.08]   # the neck, not hair ends at that height
    axis = (ring[:, :2].min(0) + ring[:, :2].max(0)) / 2
    ang = np.arctan2(ring[:, 1] - axis[1], ring[:, 0] - axis[0]); rad = np.linalg.norm(ring[:, :2] - axis, axis=1)
    NB = 36
    bins = ((ang + np.pi) / (2 * np.pi) * NB).astype(int) % NB
    prof = np.array([np.median(rad[bins == k]) if (bins == k).any() else np.nan for k in range(NB)])
    ok = ~np.isnan(prof)
    prof = np.interp(np.arange(NB), np.arange(NB)[ok], prof[ok], period=NB)
    prof = np.maximum(prof, 0.8 * np.median(prof))    # a sparse bin (3 mm) pinched the old neck into a throat ridge

    def ring_r(a):
        x = (a + np.pi) / (2 * np.pi) * NB - 0.5
        return float(np.interp(x, np.arange(NB), prof, period=NB))

    o = parts[cut['piece']]
    b = bmesh.new(); b.from_mesh(o.data)
    nf = len(b.faces)
    bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], plane_co=(0, 0, zc), plane_no=(0, 0, 1),
                           clear_outer=True)
    bmesh.ops.delete(b, geom=[v for v in b.verts if not v.link_faces], context='VERTS')
    tapered = 0
    for v in b.verts:
        if TAPER <= 0 or v.co.z < zc - TAPER:
            continue
        d = np.array([v.co.x - axis[0], v.co.y - axis[1]]); r = float(np.linalg.norm(d))
        goal = ring_r(math.atan2(d[1], d[0])) - (0.0 if WELD else INSET)
        if abs(r - goal) > 0.05 or (r <= goal and not WELD):    # welded: widen a narrower old neck too
            continue
        w = (v.co.z - (zc - TAPER)) / TAPER; w = w * w * (3 - 2 * w)
        nr = r + (goal - r) * w
        v.co.x = axis[0] + d[0] / r * nr; v.co.y = axis[1] + d[1] / r * nr; tapered += 1
    b.to_mesh(o.data); b.free()
    print('BODY part', o.name, 'bisected at z', round(zc, 4), 'faces', nf, '->', len(o.data.polygons), 'neck verts tapered',
          tapered, 'head neck ring radius', round(float(prof.min()), 4), '..', round(float(prof.max()), 4))
for i, o in parts.items():
    if EXT and i == EXT['shell']:                       # the extended neck passes through the collar on purpose
        continue
    b = bmesh.new(); b.from_mesh(o.data)
    doomed = set()
    for f in b.faces:
        c = np.array(f.calc_center_median())
        if c[2] > z0 + 0.005 and np.all((c > hlo) & (c < hhi)) and all(inside_head(v.co)[0] for v in f.verts):
            doomed.add(f)
    deleted += len(doomed)
    bmesh.ops.delete(b, geom=list(doomed), context='FACES')
    bmesh.ops.delete(b, geom=[v for v in b.verts if not v.link_faces], context='VERTS')
    moved = 0
    if doomed:
        for v in {v for e in b.edges if e.is_boundary for v in e.verts}:
            inside, loc, nrm = inside_head(v.co)
            if (v.co - loc).length <= NEAR and not inside:
                v.co = loc - nrm * INSET; moved += 1
    b.to_mesh(o.data); b.free()
    if doomed:
        print('BODY part', o.name, 'faces inside the head deleted', len(doomed), 'rim verts pulled inside it', moved)
for i in [i for i, o in parts.items() if len(o.data.polygons) == 0]:
    bpy.data.objects.remove(parts.pop(i), do_unlink=True)
for k, spec in P.get('hidden_in', {}).items():       # an old part running through a closed garment shell (the neck's
    outer, above = (spec, None) if isinstance(spec, int) else (spec['shell'], spec.get('above_z'))   # chest inside the
    o, g = parts[int(k)], parts[int(outer)]           # tunic poked out at the collar, the trousers' waist below the belt): faces
    gb = BVHTree.FromObject(g, bpy.context.evaluated_depsgraph_get(), deform=False)    # inside the shell are deleted
    b = bmesh.new(); b.from_mesh(o.data); b.verts.ensure_lookup_table()
    ins = {}
    for v in b.verts:
        loc, nrm, _, d = gb.find_nearest(v.co)
        ins[v] = loc is not None and (v.co - loc).dot(nrm) < 0.002
    gone = [f for f in b.faces if all(ins[v] for v in f.verts) and (above is None or f.calc_center_median().z > above)]
    bmesh.ops.delete(b, geom=gone, context='FACES')
    bmesh.ops.delete(b, geom=[v for v in b.verts if not v.link_faces], context='VERTS')
    comps, seen = [], set()                           # keep the largest connected piece (the visible neck and V)
    for f in b.faces:
        if f in seen:
            continue
        st, comp = [f], []
        seen.add(f)
        while st:
            x = st.pop(); comp.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y not in seen:
                        seen.add(y); st.append(y)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    stray = [f for c in comps[1:] for f in c if len(c) < 0.05 * len(b.faces)]   # small leftovers only (two legs stay)
    bmesh.ops.delete(b, geom=stray, context='FACES')
    bmesh.ops.delete(b, geom=[v for v in b.verts if not v.link_faces], context='VERTS')
    b.to_mesh(o.data); b.free()
    print('BODY part', o.name, 'faces hidden in', g.name, 'deleted', len(gone), 'stray islands', len(comps) - 1,
          'faces', len(stray), 'left', len(o.data.polygons))
CL = P.get('collar')                                   # pm3: the tunic's collar rose to the hairline at the back
if CL:
    o = parts[CL['piece']]; n = 0
    for v in o.data.vertices:
        if v.co.z > CL['above_z'] and v.co.y > CL.get('y_min', 0.0):
            w = min(1.0, (v.co.y - CL.get('y_min', 0.0)) / 0.03)
            v.co.z = CL['above_z'] + (v.co.z - CL['above_z']) * (1 - w * (1 - CL['factor'])); n += 1
    print('BODY collar verts lowered', n)
for k, n in P.get('fill_holes', {}).items():           # pinholes of the Smart Topology return (tunic collar)
    o = parts[int(k)]
    b = bmesh.new(); b.from_mesh(o.data)
    r = bmesh.ops.holes_fill(b, edges=[e for e in b.edges if e.is_boundary], sides=int(n))
    b.to_mesh(o.data); b.free()
    print('BODY part', o.name, 'holes filled', len(r['faces']))

# ---- head neck band under the body surface; braid re-seated over the body's back -----------------------------------
dg = bpy.context.evaluated_depsgraph_get()
bvhs = [BVHTree.FromObject(o, dg, deform=False) for o in parts.values()]
# the neck band only meets the old neck it is grafted onto: against every part, the throat snapped down onto the
# tunic's V collar 4 cm away and the jaw ran down into a beak
band_bvhs = [BVHTree.FromObject(parts[cut['piece']], dg, deform=False)] if cut else bvhs


def nearest_body(p, trees=None):
    best = None
    for t in (trees or bvhs):
        loc, nrm, _, d = t.find_nearest(p)
        if loc is not None and (best is None or d < best[2]):
            best = (loc, nrm, d)
    return best


pulled = seated = 0
for v in head.data.vertices:
    if v.index in lift:                              # braid: same height above our body as above Meshy's bust
        best = nearest_body(v.co)
        if best is None or best[2] > 0.12:
            continue
        if (v.co - best[0]).dot(best[1]) < lift[v.index]:     # sunk into the back: lifted out along the normal
            v.co = best[0] + best[1] * (lift[v.index] + INSET); seated += 1
        continue
    w = 0.0 if WELD or EXT else 1.0 - (v.co.z - z0) / BAND   # welded / extended into the clothing: no pull
    if w <= 0:
        continue
    best = nearest_body(v.co, band_bvhs)
    if best is None or best[2] > 0.04 or (v.co - best[0]).dot(best[1]) <= -INSET:
        continue
    w = w * w * (3 - 2 * w)
    v.co = v.co.lerp(best[0] - best[1] * INSET, w); pulled += 1
print('HEAD neck band verts pulled under the body surface', pulled, 'braid verts lifted clear of the body', seated)

# ---- renumber: kept parts in their old order, the head last ----------------------------------------------------------
mapping = {}
for n, i in enumerate(sorted(parts)):
    mapping[i] = n; parts[i].name = parts[i].data.name = f'P{n:02d}'
head.name = head.data.name = f'P{len(parts):02d}'
json.dump({'old_to_new': {str(k): v for k, v in mapping.items()}, 'head': len(parts), 'faces_deleted': deleted,
           'braid_verts': len(lift), 'weld': WELD, 'neck_piece': mapping.get(cut['piece']) if cut else None, 'z_cut': Z_CUT,
           'z_seam': Z_SEAM if EXT else Z_CUT, 'neck_uv': NECK_UV if EXT else None,
           'head_matrix': [list(r) for r in HEAD_MATRIX]}, open(os.path.join(common.WORK, 'graft.json'), 'w'), indent=1)
print('GRAFT parts', len(parts) + 1, 'head piece', len(parts), 'map', mapping)
# Meshy's GLBs import with their own custom split normals, the head's flat per face: they override smooth shading, so
# the head rendered faceted ("clay", grey smudges) and the normals jumped at the graft. Every part shades smooth now.
cleared = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.data.has_custom_normals:
        for x in bpy.context.view_layer.objects:
            x.select_set(x is o)
        bpy.context.view_layer.objects.active = o
        bpy.ops.mesh.customdata_custom_splitnormals_clear(); cleared.append(o.name)
print('NORMALS custom split normals cleared on', cleared)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'st_v1_parts.blend'))
if TAG:
    scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
    scene.display.shading.color_type = 'TEXTURE'          # the head with its Meshy texture, the body plain
    common.render_views(os.path.join(common.REVIEW, f'graft_{TAG}'), eye_old[2] - 0.08, 0.5,
                        views=('front', 'left', 'back', 'three_quarter'), resolution=(600, 600))
    scene.display.shading.color_type = 'MATERIAL'
    hm = bpy.data.materials.new('GraftHead'); hm.diffuse_color = (0.95, 0.75, 0.6, 1)
    head.data.materials[0] = hm
    common.render_views(os.path.join(common.REVIEW, f'graft_{TAG}_body'), 0.85, 1.75, views=('front', 'left'),
                        resolution=(500, 800))
