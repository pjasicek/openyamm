"""Textured static export of the rigged master (five-finger hands + head set, 2026-10-30) for clips_mm9.py.

Args: <blend> <out glb> <mesh name> <body texture prefix> <head prefix> [<head set file prefix>]
(head set files default to the head prefix; the texture pass names them <prefix>_tp, the config stays head_<head>)
Body faces: the composed body maps (../textures/<body>_*). Head and hand faces (`head` or `hand` = 1): the head set
(textures/<head>_head_*), their HeadUV copied into the single UV layer; material <mesh name>Head (merged into the
body atlas by tools/merge_head_material.py). Smooth normals; the armature node is lifted so model y = 0 is the floor.

Head cleanup (2026-10-30, user review of Annud v2: neck holes and jagged strips at the eyes and lips), from the
optional `export_fix` block of scripts/head_<head prefix>.json; part numbers are head_split.py's (loose parts ordered
by their lowest vertex index):
- `drop_parts`: loose head parts deleted (Meshy's separate eyeballs: the head shell already carries the painted eyes,
  and the eyeball cups poke through the lower lids with lid skin painted on them, the jagged strips under the eyes);
- `fill_holes_max_edges`: head boundary loops (with `fill_body_holes`, any loops) up to this many edges are filled
  (Meshy left holes in the neck and the back); the
  patch samples the centre texel of the largest face around the hole (inside one UV island: no stretch across a
  seam, no gutter texels), no new vertices or weights; the rim and its one-ring are relaxed (the holes sit in small
  dents that shaded as a notch once filled); `fill_texel: median` samples the rim face whose centre texel is nearest
  the rim's median colour instead of the largest rim face (Meshy can paint a hole's rim dark);
- `mouth_cap` [x, y, z]: the boundary loop at the back of the mouth slit nearest this point (Blender rest
  coordinates, within 2 cm) is capped (the slit showed the background through the head), and the cap plus the
  slit's inner lip faces (not facing forward, within `mouth_radius` of the cap) sample one dark texel of the head set
  (the darkest decile of their own texels), so the lips meet at a dark line instead of jagged teeth strips.
"""
import bpy, bmesh, json, sys, os
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, NAME, BODY, HEAD = argv[:5]
HEADTEX = argv[5] if len(argv) > 5 else HEAD     # head set file prefix (texture pass: <prefix>_tp)
V2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TB = os.path.join(V2, 'textures')     # mm9_peasantm1: one project folder (Annud: body maps one level up)
TH = os.path.join(V2, 'textures')
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)
for b in rig.pose.bones:
    b.matrix_basis.identity()
me = body.data


def parts_of(bm):
    """Loose parts by vertex connectivity, numbered by their lowest vertex index (as head_split.py)."""
    bm.verts.ensure_lookup_table()
    comp = -np.ones(len(bm.verts), np.int32)
    cid = 0
    for v in bm.verts:
        if comp[v.index] >= 0:
            continue
        st = [v]; comp[v.index] = cid
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if comp[y.index] < 0:
                    comp[y.index] = cid; st.append(y)
        cid += 1
    return comp


def boundary_loops(bm, faces_ok):
    seen, loops = set(), []
    for e in bm.edges:
        if not e.is_boundary or e.index in seen or not faces_ok(e.link_faces[0]):
            continue
        loop, st = [], [e]
        while st:
            x = st.pop()
            if x.index in seen:
                continue
            seen.add(x.index); loop.append(x)
            for v in x.verts:
                st += [y for y in v.link_edges if y.is_boundary and y.index not in seen]
        loops.append(loop)
    return loops


def ndimage_blur(m, r=2):
    """Box blur (radius r texels, two passes) of a mask: a soft edge for a texture repaint."""
    for _ in range(2):
        k = np.ones(2 * r + 1, np.float32) / (2 * r + 1)
        m = np.apply_along_axis(lambda x: np.convolve(x, k, 'same'), 0, m)
        m = np.apply_along_axis(lambda x: np.convolve(x, k, 'same'), 1, m)
    return np.maximum(m * 2, 0)


def face_texels(f, layer, px):
    """Base colour texels on a 4 x 4 barycentric grid of a triangle (first three corners)."""
    H, W = px.shape[:2]
    uv = [np.array(tuple(l[layer].uv)) for l in f.loops[:3]]
    out = []
    for i in range(4):
        for j in range(4 - i):
            w = np.array([i + 0.33, j + 0.33, 3.34 - i - j]) / 4.0
            u, v = w[0] * uv[0] + w[1] * uv[1] + w[2] * uv[2]
            out.append(px[min(H - 1, max(0, int(v * H))), min(W - 1, max(0, int(u * W))), :3])
    return np.array(out)


PIXELS = {}


def texels_of(head):
    """Base colour pixels of the head set (head faces) or the body set (body faces), loaded once."""
    if head not in PIXELS:
        path = os.path.join(TH, f'{HEADTEX}_head_basecolor.png') if head else \
            os.path.join(TB, f'{BODY}_basecolor_graded.png')
        img = bpy.data.images.load(path, check_existing=True)
        px = np.empty(img.size[0] * img.size[1] * 4, np.float32)
        img.pixels.foreach_get(px)
        PIXELS[head] = px.reshape(img.size[1], img.size[0], 4)
    return PIXELS[head]


def median_face(ring, lh, uvs):
    """`fill_texel: median` (texture pass 2026-10-30, Annud: Meshy paints the rim of a hole dark, so the largest rim
    face's centre texel put a brown patch on the neck): the rim face whose centre texel is nearest the rim's median."""
    cols = []
    for f in ring:
        layer = uvs[0] if f[lh] == 1 else uvs[1]
        px = texels_of(f[lh] == 1)
        H, W = px.shape[:2]
        c = sum(np.array(tuple(l[layer].uv)) for l in f.loops[:3]) / 3
        cols.append(px[min(H - 1, int(c[1] * H)), min(W - 1, int(c[0] * W)), :3])
    med = np.median(np.array(cols), 0)
    return min(zip(ring, cols), key=lambda fc: float(np.linalg.norm(fc[1] - med)))[0]


HEAD_BASE = [None]          # head base colour file the GLB embeds (the mouth repaint writes its own copy)


def head_fix(fix):
    mw = body.matrix_world
    bm = bmesh.new(); bm.from_mesh(me)
    lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
    uvs = [bm.loops.layers.uv[n] for n in ('HeadUV', 'UVMap')]
    comp = parts_of(bm)
    drop = set(fix.get('drop_parts', []))
    gone = [f for f in bm.faces if comp[f.verts[0].index] in drop]
    rep = {'dropped_faces': len(gone)}
    bmesh.ops.delete(bm, geom=gone, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.verts.index_update(); bm.edges.index_update()
    filled, cap = [], []
    target = fix.get('mouth_cap')
    loops = boundary_loops(bm, lambda f: f[lh] == 1 or fix.get('fill_body_holes', False))
    mouth = None
    if target is not None:
        dist = lambda lp: np.linalg.norm(np.mean([tuple(mw @ v.co) for e in lp for v in e.verts], 0) - target)
        best = min(loops, key=dist)
        if dist(best) < 0.02:
            mouth = best
        else:
            raise SystemExit(f'mouth_cap: no head boundary loop within 2 cm of {target}')
    for lp in loops:
        small = len(lp) <= fix.get('fill_holes_max_edges', 0)
        if not small and lp is not mouth:
            continue
        ring = {e.link_faces[0] for e in lp}
        ref = max(ring, key=lambda f: f.calc_area())
        if fix.get('fill_texel') == 'median' and lp is not mouth:
            ref = median_face(ring, lh, uvs)
        new = bmesh.ops.holes_fill(bm, edges=lp, sides=0)['faces']
        if not new:                                    # mm9_peasantm7: holes_fill returned nothing for a 5-edge
            vs = [lp[0].verts[0], lp[0].verts[1]]      # elbow hole; one face from the ordered rim instead
            left = set(lp[1:])
            while left:
                e = next((e for e in left if vs[-1] in e.verts), None)
                if e is None:
                    break
                left.discard(e)
                nv = e.other_vert(vs[-1])
                if nv is vs[0]:
                    break
                vs.append(nv)
            f0 = lp[0].link_faces[0]                   # wind the cap against the rim face that owns the first edge
            l0 = next(l for l in f0.loops if l.edge is lp[0])
            if l0.vert is vs[0]:
                vs.reverse()
            try:
                new = [bm.faces.new(vs)] if len(vs) >= 3 else []   # mm9_peasantboy: a 1-edge 'loop' (open sliver)
            except ValueError:
                new = []
        new = bmesh.ops.triangulate(bm, faces=new, quad_method='BEAUTY', ngon_method='BEAUTY')['faces']
        for f in new:
            f[lh] = ref[lh] if lp is not mouth else 1; f[lk] = 0
            for l in f.loops:
                for u in uvs:
                    l[u].uv = tuple(sum((np.array(tuple(x[u].uv)) for x in ref.loops), np.zeros(2)) / len(ref.loops))
        if lp is not mouth:                            # Meshy's holes sit in small dents: relax the rim and its ring
            ring = {v for e in lp for v in e.verts}
            ring |= {e.other_vert(v) for v in list(ring) for e in v.link_edges}
            for _ in range(4):
                bmesh.ops.smooth_vert(bm, verts=list(ring), factor=0.5, use_axis_x=True, use_axis_y=True,
                                      use_axis_z=True)
        (cap if lp is mouth else filled).extend(new)
        rep.setdefault('filled_loops' if lp is not mouth else 'mouth_loop', []).append(len(lp))
    if cap:
        c = np.mean([tuple(mw @ f.calc_center_median()) for f in cap], 0)
        R = fix.get('mouth_radius', 0.025)
        nrm = lambda f: (mw.to_3x3() @ f.normal).normalized()
        slit, st = set(cap), list(cap)
        while st:                                      # inner lip faces reachable from the cap, not facing forward
            f = st.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g in slit or g[lh] != 1 or nrm(g).y < -0.35:
                        continue
                    if np.linalg.norm(np.array(tuple(mw @ g.calc_center_median())) - c) > R:
                        continue
                    slit.add(g); st.append(g)
        img = bpy.data.images.load(os.path.join(TH, f'{HEADTEX}_head_basecolor.png'), check_existing=True)
        H, W = img.size[1], img.size[0]
        px = np.empty(H * W * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H, W, 4)
        lum = lambda t: t @ np.array([0.299, 0.587, 0.114])
        near = [g for g in bm.faces if g[lh] == 1 and g not in slit
                and np.linalg.norm(np.array(tuple(mw @ g.calc_center_median())) - c) < R]
        # UV footprint of the lips around the slit; the reference smile's teeth were painted there as a pale band
        # along the lips' jagged inner edges: those texels take the lips' own median colour
        foot = np.zeros((H, W), bool)
        for g in near:
            uv = np.array([tuple(l[uvs[0]].uv) for l in g.loops[:3]]) * (W, H)
            lo, hi = np.floor(uv.min(0)).astype(int) - 1, np.ceil(uv.max(0)).astype(int) + 2
            xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], W)), np.arange(max(lo[1], 0), min(hi[1], H)))
            p = np.stack([xs + 0.5, ys + 0.5], -1)
            T = np.array([uv[1] - uv[0], uv[2] - uv[0]]).T
            if abs(np.linalg.det(T)) < 1e-9:
                continue
            st = (p - uv[0]) @ np.linalg.inv(T).T
            inside = (st[..., 0] >= -0.02) & (st[..., 1] >= -0.02) & (st.sum(-1) <= 1.04)
            foot[ys[inside], xs[inside]] = True
        rgb = px[..., :3]
        pale = foot & (lum(rgb) > 0.62) & (rgb[..., 0] - rgb[..., 2] < 0.32)    # teeth: light and less red than lips
        lip = foot & ~pale & (rgb[..., 0] > rgb[..., 1] * 1.25) & (lum(rgb) > 0.3)
        lip_rgb = np.median(rgb[lip], 0)
        soft = np.clip(ndimage_blur(pale.astype(np.float32)), 0, 1)
        rgb_new = rgb * (1 - soft[..., None]) + lip_rgb * soft[..., None]
        px[..., :3] = np.where(foot[..., None], rgb_new, rgb)
        img.pixels.foreach_set(px.ravel())
        img.filepath_raw = os.path.join(V2, 'work', f'{HEADTEX}_head_basecolor_export.png')   # the GLB embeds this file
        img.file_format = 'PNG'
        img.save()
        HEAD_BASE[0] = img.filepath_raw
        tx = np.concatenate([face_texels(g, uvs[0], px) for g in slit if g not in cap])
        dark_rgb = tx[np.argsort(lum(tx))[len(tx) // 20]]
        best = None                                    # the slit colour: nearest texel colour at a face centre
        for g in list(slit - set(cap)) + near:
            cuv = sum(np.array(tuple(l[uvs[0]].uv)) for l in g.loops[:3]) / 3
            d = np.linalg.norm(px[int(cuv[1] * H), int(cuv[0] * W), :3] - dark_rgb)
            if best is None or d < best[0]:
                best = (d, tuple(cuv))
        for f in slit:
            for l in f.loops:
                for u in uvs:
                    l[u].uv = best[1]
        rep.update(mouth_slit_faces=len(slit), mouth_cap_faces=len(cap), mouth_lip_faces=len(near),
                   teeth_texels_repainted=int(pale.sum()), lip_rgb=[round(float(x), 3) for x in lip_rgb],
                   mouth_dark_rgb=[round(float(x), 3) for x in dark_rgb])
    rep['filled_faces'] = len(filled)
    bm.to_mesh(me); bm.free(); me.update()
    print('HEADFIX', json.dumps(rep))


cfg = os.path.join(V2, 'scripts', f'head_{HEAD}.json')
if os.path.exists(cfg) and json.load(open(cfg)).get('export_fix'):
    head_fix(json.load(open(cfg))['export_fix'])
nf = len(me.polygons)
hd = np.zeros(nf, np.int32); hn = np.zeros(nf, np.int32)
me.attributes['head'].data.foreach_get('value', hd)
me.attributes['hand'].data.foreach_get('value', hn)
sel = (hd | hn).astype(bool)
huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
for p in me.polygons:
    if sel[p.index]:
        for li in p.loop_indices:
            buv[li].uv = huv[li].uv
me.uv_layers.active = me.uv_layers['UVMap']
for ln in [l.name for l in me.uv_layers if l.name != 'UVMap']:
    me.uv_layers.remove(me.uv_layers[ln])


def material(name, folder, base, normal, mr):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(fname, cs):
        img = bpy.data.images.load(os.path.join(folder, fname), check_existing=True)
        img.colorspace_settings.name = cs
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = img
        return n
    nt.links.new(tex(base, 'sRGB').outputs['Color'], bsdf.inputs['Base Color'])
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tex(normal, 'Non-Color').outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(tex(mr, 'Non-Color').outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


me.materials.clear()
me.materials.append(material(NAME, TB, f'{BODY}_basecolor_graded.png', f'{BODY}_normal_1k.png', f'{BODY}_metal_rough_1k.png'))
me.materials.append(material(NAME + 'Head', TH, HEAD_BASE[0] or f'{HEADTEX}_head_basecolor.png',
                             f'{HEADTEX}_head_normal_1k.png', f'{HEADTEX}_head_metal_rough_1k.png'))
me.polygons.foreach_set('material_index', sel.astype(np.int32).tolist())
for at in [a.name for a in me.attributes if a.name in ('head', 'hand', 'graft_s', 'graft_side')]:
    me.attributes.remove(me.attributes[at])
for g in [g for g in body.vertex_groups if g.name.startswith('MP_')]:
    body.vertex_groups.remove(g)
# mm9_krohn: the glaive and sword (object 'Props', add_props.py) join the body as a third material (props atlas)
props = bpy.data.objects.get('Props')
if props is not None:
    props.data.materials.clear()
    props.data.materials.append(material(NAME + 'Props', TB, 'props_basecolor.png', 'props_normal.png', 'props_orm.png'))
    for o in bpy.data.objects:
        o.select_set(o in (body, props))
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    me = body.data
    print('PROPS joined', len(me.polygons))
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
try:
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
except RuntimeError:
    pass
bpy.ops.object.shade_smooth()
lift = -min((body.matrix_world @ v.co).z for v in me.vertices)
rig.location.z += lift
bpy.context.view_layer.update()
print('LIFT', round(lift, 4))
body.name = NAME
me.name = NAME
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_animations=False,
                          export_skins=True, export_yup=True, export_image_format='AUTO', export_attributes=False)
print('EXPORTED', OUT, len(me.polygons), 'head/hand faces', int(sel.sum()))
