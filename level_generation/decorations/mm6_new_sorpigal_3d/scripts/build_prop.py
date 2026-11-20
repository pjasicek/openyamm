"""Build one static decoration prop from a Poly Haven scan: LOD0..3 meshes, baked 1024 textures, linked GLB.
Args: <prop> where prop is a key of props.json (rock, barrel). Writes <prop>/work/<prop>_lods.blend,
<prop>/work/textures/*.png, <prop>/work/<prop>_export.glb, and prints BUILD lines.

Modes
 - decimate (rock): the merged scan is collapse-decimated to the LOD0 budget, gets a fresh Smart UV unwrap, and
   LOD1..3 are collapse-decimated from LOD0 (they keep LOD0's UVs and textures).
 - lathe (barrel): the scan is built from separate stave/hoop shells that crack under decimation, so each LOD is a
   lathed proxy of the scan's radial profile (outer wall, top chime rim recessed to the lid, flat base). Every LOD uses
   the same UV layout function, so all LODs share one texture set. With rim.open the recessed levels have no lid but
   an inner wall and floor, added after the bake on texture already there (see open_top).
All maps are baked from the full-detail scan in Cycles (selected to active): normal (scan normal map included), base
colour (emission of the diffuse map), roughness / metal / AO (channels of the scan's ARM map). AO is folded into the
base colour; grading per props.json brings the albedo toward the native sprite. The metallic-roughness image holds
R = 0 (an open barrel: the specular mask), G = roughness, B = metal."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Euler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deco_common as dc

PROP = sys.argv[sys.argv.index('--') + 1]
# PROPS_JSON / PROP_ROOT let other prop sets (props/) reuse this builder with their own configs and folders.
CFG = json.load(open(os.environ.get('PROPS_JSON', os.path.join(dc.PROJECT, 'scripts', 'props.json'))))[PROP]
ROOT = os.environ.get('PROP_ROOT', os.path.join(dc.PROJECT, PROP))
WORK = os.path.join(ROOT, 'work'); TEX = os.path.join(WORK, 'textures')
os.makedirs(TEX, exist_ok=True)
RES = CFG.get('texture_size', 1024)

dc.reset()
scene = bpy.context.scene
objs = [o for o in dc.import_gltf(os.path.join(ROOT, CFG['source'])) if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1:
    bpy.ops.object.join()
high = bpy.context.view_layer.objects.active; high.name = 'High'
high.rotation_mode = 'XYZ'                       # the glTF importer leaves quaternion mode
high.rotation_euler = (0, 0, math.radians(CFG.get('yaw_deg', 0)))
high.scale = CFG.get('scale', [1, 1, 1])
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
lo, hi = dc.world_bounds([high])
high.data.transform(Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))))
high.data.update()
# Optional extra scans joined to the main one (rock07: a flat slab resting on the boulder). Each part is centred on
# its own bounds, then rotated (degrees), scaled and moved to `location` in the grounded main scan's frame.
for part in CFG.get('parts', []):
    pobjs = [o for o in dc.import_gltf(os.path.join(ROOT, part['source'])) if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in pobjs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = pobjs[0]
    bpy.ops.object.join()
    piece = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    plo, phi = dc.world_bounds([piece])
    piece.data.transform(Matrix.Translation(-(plo + phi) / 2))
    piece.data.transform(Matrix.LocRotScale(Vector(part['location']),
                                            Euler([math.radians(a) for a in part.get('rotation_deg', [0, 0, 0])]),
                                            Vector(part.get('scale', [1, 1, 1]))))
    bpy.ops.object.select_all(action='DESELECT'); piece.select_set(True); high.select_set(True)
    bpy.context.view_layer.objects.active = high
    bpy.ops.object.join()
if CFG.get('parts'):
    lo, hi = dc.world_bounds([high])
    high.data.transform(Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))))
    high.data.update()
peak = CFG.get('peak')
if peak:
    # Optional reshaping before the bake (surf rocks): heights scale by base + lift x a Gaussian bump centred at
    # (x, y) as fractions of the half extents, width as a fraction of the larger half extent.
    lo, hi = dc.world_bounds([high]); half = (hi - lo) / 2
    cx, cy = peak['x'] * half.x, peak['y'] * half.y; width = peak['width'] * max(half.x, half.y)
    for v in high.data.vertices:
        bump = math.exp(-((v.co.x - cx) ** 2 + (v.co.y - cy) ** 2) / (width * width))
        v.co.z *= peak['base'] + peak['lift'] * bump
    high.data.update()
lo, hi = dc.world_bounds([high])
print('BUILD high', PROP, 'tris', sum(len(p.vertices) - 2 for p in high.data.polygons), 'size', [round(v, 3) for v in hi - lo])


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def new_object(name, mesh):
    obj = bpy.data.objects.new(name, mesh); scene.collection.objects.link(obj); return obj


def decimate_to(obj, target):
    """Collapse-decimate (triangulated) until the triangle count is within the budget."""
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    start = triangles(obj); ratio = target / start
    for _ in range(12):
        mod = obj.modifiers.new('Decimate', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
        mod.ratio = ratio; mod.use_collapse_triangulate = True
        depsgraph = bpy.context.evaluated_depsgraph_get()
        count = sum(len(p.vertices) - 2 for p in obj.evaluated_get(depsgraph).data.polygons)
        if count <= target:
            bpy.ops.object.modifier_apply(modifier=mod.name)
            return count
        obj.modifiers.remove(mod); ratio *= target / count * 0.995
    raise RuntimeError(f'cannot decimate {obj.name} to {target}')


# ---------------------------------------------------------------- LOD meshes
names = [CFG['name']] + [f"{CFG['name']}_LOD{i}" for i in (1, 2, 3)]
lods = []
if CFG['mode'] == 'decimate':
    me = high.data.copy(); bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    bm.to_mesh(me); bm.free()
    lod0 = new_object(names[0], me)
    while lod0.data.uv_layers:
        lod0.data.uv_layers.remove(lod0.data.uv_layers[0])
    lod0.data.materials.clear()
    if CFG.get('parts'):
        # Fuse the joined scans into one closed surface (voxel remesh) so the dome unwrap below still finds a single
        # visible island and no triangles are spent on the hidden contact faces; the bake still reads the scans.
        bpy.ops.object.select_all(action='DESELECT'); lod0.select_set(True); bpy.context.view_layer.objects.active = lod0
        mod = lod0.modifiers.new('Remesh', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = CFG.get('voxel', 0.006)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        print('BUILD remeshed tris', triangles(lod0))
    decimate_to(lod0, CFG['targets'][0])
    lod0.data.uv_layers.new(name='UVMap')
    bpy.ops.object.select_all(action='DESELECT'); lod0.select_set(True); bpy.context.view_layer.objects.active = lod0
    # Dome unwrap: one seam round the flat underside, so the visible surface is a single island and the LOD
    # collapses below never smear texels across island borders (they only meet at the hidden base).
    bm = bmesh.new(); bm.from_mesh(lod0.data); bm.faces.ensure_lookup_table()
    zmax = max(v.co.z for v in bm.verts)
    bottom = {f for f in bm.faces if f.normal.z < -0.5 and f.calc_center_median().z < 0.25 * zmax}
    grow = True                                   # keep the largest connected underside patch only
    seeds = sorted(bottom, key=lambda f: f.calc_center_median().z)[:1]
    patch = set(seeds); stack = list(seeds)
    while stack:
        f = stack.pop()
        for e in f.edges:
            for g in e.link_faces:
                if g in bottom and g not in patch:
                    patch.add(g); stack.append(g)
    for e in bm.edges:
        e.seam = len(e.link_faces) == 2 and ((e.link_faces[0] in patch) != (e.link_faces[1] in patch))
    bm.to_mesh(lod0.data); bm.free()
    print('BUILD underside faces', len(patch), 'seam edges', sum(e.use_seam for e in lod0.data.edges))
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='MINIMUM_STRETCH', margin=0.01)
    bpy.ops.uv.pack_islands(rotate=True, margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')
    lods.append(lod0)
    for level in (1, 2, 3):
        lod = new_object(names[level], lod0.data.copy())
        decimate_to(lod, CFG['targets'][level])
        lods.append(lod)
    band = CFG.get('ground_band')
    if band:
        # Collapse lifts the flat base on the coarser levels (2-3 cm on rock07/rock14); lower each level's bottom
        # band back onto the ground, fading to no change at `band` metres up, so no level floats.
        for lod in lods:
            zmin = min(v.co.z for v in lod.data.vertices)
            for v in lod.data.vertices:
                if v.co.z < band:
                    v.co.z -= zmin * (1 - v.co.z / band)
            lod.data.update()
else:
    # radial profile r(z) of the scan: maximum radius per height bin
    pts = np.array([v.co[:] for v in high.data.vertices])
    rad = np.hypot(pts[:, 0], pts[:, 1]); z = pts[:, 2]
    ztop = float(z.max()); bins = 160
    edges = np.linspace(0, ztop, bins + 1); prof = np.zeros(bins)
    idx = np.clip((z / ztop * bins).astype(int), 0, bins - 1)
    np.maximum.at(prof, idx, rad)
    for i in range(bins):                        # bins without vertices take their neighbours' radius
        if prof[i] == 0:
            prof[i] = prof[max(i - 1, 0)]
    centres = (edges[:-1] + edges[1:]) / 2
    rim = CFG['rim']                             # top chime: wall thickness and lid depth below the top
    zlid = ztop - rim['lid_depth']

    def radius(zz):
        return float(np.interp(zz, centres, prof))

    def build_lathe(name, segments, rings, recess):
        bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
        side_v0, side_v1 = 0.25, 1.0
        zs = np.linspace(0.0, ztop, rings)
        circle = [(math.cos(2 * math.pi * s / segments), math.sin(2 * math.pi * s / segments)) for s in range(segments)]

        def ring(zz, r):
            return [bm.verts.new((c * r, s_ * r, zz)) for c, s_ in circle]
        outer = [ring(zz, radius(zz)) for zz in zs]
        # side wall: u around (seam duplicated through per-loop UVs), v up
        for k in range(rings - 1):
            for s in range(segments):
                a, b = outer[k][s], outer[k][(s + 1) % segments]
                c, d = outer[k + 1][(s + 1) % segments], outer[k + 1][s]
                f = bm.faces.new((a, b, c, d))
                u0, u1 = s / segments, (s + 1) / segments
                v0 = side_v0 + (side_v1 - side_v0) * zs[k] / ztop; v1 = side_v0 + (side_v1 - side_v0) * zs[k + 1] / ztop
                for loop, (uu, vv) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                    loop[uv].uv = (uu, vv)
        top = outer[-1]
        rtop = radius(ztop)

        def disc_uv(x, y, cx, cy, size, rmax):
            return (cx + x / rmax * size, cy + y / rmax * size)
        if recess:
            rin = rtop - rim['thickness']
            inner_top = ring(ztop, rin); inner_low = ring(zlid, rin)
            # rim top and inner wall: thin strip v in [0.2, 0.245]
            for strip, (A, B, va, vb) in enumerate(((top, inner_top, 0.245, 0.235), (inner_top, inner_low, 0.235, 0.205))):
                for s in range(segments):
                    a, b = A[s], A[(s + 1) % segments]; c, d = B[(s + 1) % segments], B[s]
                    f = bm.faces.new((a, b, c, d))
                    u0, u1 = s / segments, (s + 1) / segments
                    for loop, (uu, vv) in zip(f.loops, ((u0, va), (u1, va), (u1, vb), (u0, vb))):
                        loop[uv].uv = (uu, vv)
            lid_ring, lid_z, lid_r = inner_low, zlid, rin
        else:
            lid_ring, lid_z, lid_r = top, ztop, rtop
        centre = bm.verts.new((0, 0, lid_z))
        for s in range(segments):
            a, b = lid_ring[s], lid_ring[(s + 1) % segments]
            f = bm.faces.new((a, b, centre))
            for loop in f.loops:
                p = loop.vert.co
                loop[uv].uv = disc_uv(p.x, p.y, 0.1, 0.1, 0.095, rtop)
        bottom_centre = bm.verts.new((0, 0, 0))
        for s in range(segments):
            a, b = outer[0][(s + 1) % segments], outer[0][s]
            f = bm.faces.new((a, b, bottom_centre))
            for loop in f.loops:
                p = loop.vert.co
                loop[uv].uv = disc_uv(p.x, p.y, 0.32, 0.1, 0.095, radius(0.0))
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        obj = new_object(name, me)
        for p in obj.data.polygons:
            p.use_smooth = True
        return obj
    for level, (segments, rings, recess) in enumerate(CFG['lathe_levels']):
        lods.append(build_lathe(names[level], segments, rings, recess))
    # hard edges at the rim and the base keep their silhouette crisp: split normals by angle
    for obj in lods:
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
for obj in lods:
    print('BUILD lod', obj.name, 'tris', triangles(obj), 'zmin', round(min(v.co.z for v in obj.data.vertices), 4),
          'zmax', round(max(v.co.z for v in obj.data.vertices), 4))
    if CFG['mode'] == 'decimate':
        for p in obj.data.polygons:
            p.use_smooth = True

# ---------------------------------------------------------------- bake
scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
for kind in ('OPTIX', 'CUDA'):
    try:
        prefs.compute_device_type = kind; prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = 'GPU'; break
    except Exception:
        continue
scene.cycles.samples = 16
bake = scene.render.bake
bake.use_selected_to_active = True; bake.cage_extrusion = CFG['cage_extrusion']; bake.max_ray_distance = CFG['max_ray']
bake.margin = 16; bake.margin_type = 'EXTEND'
lod0 = lods[0]
target_mat = bpy.data.materials.new('BakeTarget'); target_mat.use_nodes = True
lod0.data.materials.clear(); lod0.data.materials.append(target_mat)
tnode = target_mat.node_tree.nodes.new('ShaderNodeTexImage'); target_mat.node_tree.nodes.active = tnode

# Every scan material of the high mesh (one per joined part): its output, BSDF, diffuse and ARM maps.
scans = []
for hmat in high.data.materials:
    hnt = hmat.node_tree
    images = {os.path.basename(n.image.filepath or n.image.name): n for n in hnt.nodes if n.type == 'TEX_IMAGE' and n.image}
    print('BUILD scan images', list(images))
    sep = hnt.nodes.new('ShaderNodeSeparateColor')
    hnt.links.new(next(n for k, n in images.items() if '_arm_' in k).outputs['Color'], sep.inputs['Color'])
    scans.append({'tree': hnt, 'out': next(n for n in hnt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output),
                  'bsdf': next(n for n in hnt.nodes if n.type == 'BSDF_PRINCIPLED'),
                  'diff': next(n for k, n in images.items() if '_diff_' in k).outputs['Color'], 'arm': sep})


def bake_map(name, kind, colorspace, source=None):
    """Bake one map from the scan; source picks the emitted socket of each scan material."""
    img = bpy.data.images.new(name, RES, RES, alpha=False); img.colorspace_settings.name = colorspace
    tnode.image = img
    emits = []
    if source is not None:
        for scan in scans:
            emit = scan['tree'].nodes.new('ShaderNodeEmission')
            scan['tree'].links.new(source(scan), emit.inputs['Color'])
            scan['tree'].links.new(emit.outputs['Emission'], scan['out'].inputs['Surface'])
            emits.append(emit)
    bpy.ops.object.select_all(action='DESELECT'); high.select_set(True); lod0.select_set(True)
    bpy.context.view_layer.objects.active = lod0
    bpy.ops.object.bake(type=kind)
    for scan, emit in zip(scans, emits):
        scan['tree'].links.new(scan['bsdf'].outputs['BSDF'], scan['out'].inputs['Surface'])
        scan['tree'].nodes.remove(emit)
    return img


normal = bake_map('normal', 'NORMAL', 'Non-Color')
base = bake_map('base_raw', 'EMIT', 'sRGB', lambda scan: scan['diff'])
ao = bake_map('ao', 'EMIT', 'Non-Color', lambda scan: scan['arm'].outputs['Red'])
rough = bake_map('rough', 'EMIT', 'Non-Color', lambda scan: scan['arm'].outputs['Green'])
metal = bake_map('metal', 'EMIT', 'Non-Color', lambda scan: scan['arm'].outputs['Blue'])


def px(img):
    a = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(a); return a.reshape(RES, RES, 4)


def save(img_name, rgb, colorspace):
    img = bpy.data.images.new(img_name, RES, RES, alpha=False); img.colorspace_settings.name = colorspace
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((RES, RES, 1), np.float32)], 2)
    img.pixels.foreach_set(rgba.ravel()); img.filepath_raw = os.path.join(TEX, img_name + '.png')
    img.file_format = 'PNG'; img.save(); return img


to_lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
to_srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)
b = to_lin(px(base)[..., :3])
a = px(ao)[..., :1]
b = b * (1 - CFG['ao_strength'] * (1 - a))
g = CFG.get('grade')
if g:
    luma = (b @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    if 'contrast' in g:
        # Optional (flat-albedo scans such as the moon rocks): luma contrast as a power about the mean luma.
        b = b * np.power(np.maximum(luma, 1e-5) / luma.mean(), g['contrast'] - 1)
        luma = (b @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    graded = (luma + (b - luma) * g['saturation']) * np.array(g['gain'], np.float32)   # saturation, then linear gain
    keep = px(metal)[..., :1] if g.get('skip_metal') else 0.0     # metal (barrel hoops) keeps its scanned colour
    b = graded * (1 - keep) + b * keep
base_png = save(f'{PROP}_basecolor', to_srgb(b), 'sRGB')
normal_png = save(f'{PROP}_normal', px(normal)[..., :3], 'Non-Color')
rough_px = px(rough)[..., :1]
if 'roughness_min' in CFG:                       # optional floor for glossy scans (rock_09 reads wet otherwise)
    rough_px = np.maximum(rough_px, CFG['roughness_min'])
spec_mask = np.zeros((RES, RES, 1), np.float32)
if CFG['mode'] == 'lathe' and 'open' in CFG['rim']:
    # R = specular scale (openyamm_specular_mask): full, except on the lid planks, now only the open barrel's floor,
    # which would otherwise reflect the open sky from the bottom of a dark barrel.
    texel = (np.arange(RES) + 0.5) / RES
    uu, vv = np.meshgrid(texel, texel)              # Blender pixel rows run bottom-up, as v does
    spec_mask[..., 0] = np.where(np.hypot(uu - 0.1, vv - 0.1) < 0.1, CFG['rim']['open']['floor_specular'], 1.0)
orm = np.concatenate([spec_mask, rough_px, px(metal)[..., :1]], 2)
orm_png = save(f'{PROP}_metal_rough', orm, 'Non-Color')
lin_mean = b.reshape(-1, 3).mean(0)
print('BUILD albedo linear mean', [round(float(v), 4) for v in lin_mean])

def open_top(obj, rings):
    """Open barrel (rim.open): the lid disc becomes an inner wall following the bulge and an inner floor.

    Added after the bake, because these faces reuse baked texture: the inner staves a hoop-free band of the side strip
    (stretched along the grain), the floor the lid's planks. COLOR_0 darkens them with depth, as the staves shade a
    real barrel's inside; every other corner stays white.
    """
    cfg = CFG['rim']['open']
    bm = bmesh.new(); bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.active
    color = bm.loops.layers.color.new('Color')
    for face in bm.faces:
        for loop in face.loops:
            loop[color] = (1.0, 1.0, 1.0, 1.0)
    lid = [f for f in bm.faces if all(abs(v.co.z - zlid) < 1e-5 for v in f.verts)]
    rim_ring = sorted({v for f in lid for v in f.verts if math.hypot(v.co.x, v.co.y) > 1e-4},
                      key=lambda v: math.atan2(v.co.y, v.co.x) % (2 * math.pi))
    bmesh.ops.delete(bm, geom=lid, context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    segments = len(rim_ring)
    angles = [math.atan2(v.co.y, v.co.x) for v in rim_ring]
    zfloor = cfg['floor']
    zs = np.linspace(zlid, zfloor, rings + 1)
    walls = [rim_ring] + [[bm.verts.new((math.cos(a) * (radius(zz) - rim['thickness']),
                                         math.sin(a) * (radius(zz) - rim['thickness']), zz)) for a in angles]
                          for zz in zs[1:]]
    v_top, v_bottom = cfg['stave_band']

    def shade(zz):
        depth = (zlid - zz) / (zlid - zfloor)
        return cfg['rim_shade'] + (cfg['floor_shade'] - cfg['rim_shade']) * depth ** 0.7
    for k in range(rings):
        for i in range(segments):
            a, b = walls[k][i], walls[k][(i + 1) % segments]
            c, d = walls[k + 1][(i + 1) % segments], walls[k + 1][i]
            f = bm.faces.new((a, b, c, d))
            u0, u1 = i / segments, (i + 1) / segments
            for loop, uu in zip(f.loops, (u0, u1, u1, u0)):
                zz = loop.vert.co.z
                loop[uv].uv = (uu, v_top + (v_bottom - v_top) * (zlid - zz) / (zlid - zfloor))
                loop[color] = (shade(zz),) * 3 + (1.0,)
    centre = bm.verts.new((0, 0, zfloor))
    floor_r = max(math.hypot(v.co.x, v.co.y) for v in walls[-1])
    for i in range(segments):
        f = bm.faces.new((walls[-1][(i + 1) % segments], walls[-1][i], centre))
        for loop in f.loops:
            p = loop.vert.co
            loop[uv].uv = (0.1 + p.x / floor_r * 0.085, 0.1 + p.y / floor_r * 0.085)
            loop[color] = (cfg['floor_shade'],) * 3 + (1.0,)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data); bm.free()
    obj.data.color_attributes.active_color_name = 'Color'
    for p in obj.data.polygons:
        p.use_smooth = True
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))


if CFG['mode'] == 'lathe' and 'open' in CFG['rim']:
    for obj, (segments, rings, recess) in zip(lods, CFG['lathe_levels']):
        if recess:
            open_top(obj, CFG['rim']['open']['rings'][lods.index(obj)])
            print('BUILD opened', obj.name, 'tris', triangles(obj))

# ---------------------------------------------------------------- runtime material and export
mat = bpy.data.materials.new(CFG['name']); mat.use_nodes = True
nt = mat.node_tree; pb = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(img):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n


nt.links.new(tex(base_png).outputs['Color'], pb.inputs['Base Color'])
nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal_png).outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], pb.inputs['Normal'])
sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(orm_png).outputs['Color'], sp.inputs['Color'])
nt.links.new(sp.outputs['Green'], pb.inputs['Roughness']); nt.links.new(sp.outputs['Blue'], pb.inputs['Metallic'])
for obj in lods:
    obj.data.materials.clear(); obj.data.materials.append(mat)
opened = CFG['mode'] == 'lathe' and 'open' in CFG['rim']
if opened:
    mat['openyamm_specular_mask'] = True
bpy.data.objects.remove(high, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{PROP}_lods.blend'))
out_glb = os.path.join(WORK, f'{PROP}_export.glb')
bpy.ops.object.select_all(action='DESELECT')
for obj in lods:
    obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=out_glb, use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=False, export_skins=False, export_morph=False, export_image_format='AUTO',
                          export_extras=opened, export_attributes=False,
                          export_vertex_color='NAME' if opened else 'MATERIAL', export_vertex_color_name='Color')
print('BUILD exported', out_glb, 'tris', [triangles(o) for o in lods])
