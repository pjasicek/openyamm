"""Build one MM7 scan rock from Poly Haven scans: LOD0..3 meshes, baked textures, export GLB (LODs as separate objects,
linked afterwards by tools/link_static_model_lods.py). Adapted from the MM6 scan-rock builder
(../../mm6_new_sorpigal_3d/scripts/build_prop.py, decimate mode), with these additions:
 - scans are picked by key from scans.py (a set piece by its node), and `mirror` mirrors a scan in x;
 - `rotation_deg` [x, y, z] tilts or turns the main scan before grounding (a leaning slab), and `sink` sinks it by that
   fraction of its height and cuts it flat at the ground; `post_scale` scales it in world axes after the tilt;
 - `height_m` scales the grounded rock uniformly to that height (the art height in metres), so `scale` only shapes;
 - COLOR_0 on every primitive: white, darkened toward the base by `base_shade` (the sprites' dark undersides);
 - the raw bakes are kept in work/<rock>/bake_*.npy, so `--regrade` only re-grades the albedo and re-exports.

Args: <rock> [--regrade | --preview]; settings in rocks.json. Writes work/<rock>/<rock>_lods.blend, work/<rock>/textures/*.png,
work/<rock>/<rock>_export.glb and prints BUILD lines.

LOD0 is the merged scan (voxel-remeshed when parts are joined) collapse-decimated to the budget, with one seam round the
flat underside (dome unwrap); LOD1..3 are collapsed from LOD0 and keep its UVs and textures. All maps are baked from the
full scans in Cycles (selected to active): normal, base colour, AO / roughness / metal (ARM channels). AO is folded into
the base colour, then the grade (optional luma contrast, tint mix and luma cap, saturation, linear gain) brings the albedo to the sprite."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Euler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scans

ARGS = sys.argv[sys.argv.index('--') + 1:]
ROCK = ARGS[0]
REGRADE = '--regrade' in ARGS
CFG = json.load(open(os.path.join(scans.HERE, 'rocks.json')))[ROCK]
WORK = os.path.join(scans.HERE, 'work', ROCK); TEX = os.path.join(WORK, 'textures')
os.makedirs(TEX, exist_ok=True)
RES = CFG.get('texture_size', 1024)
BLEND = os.path.join(WORK, f'{ROCK}_lods.blend')
OUT_GLB = os.path.join(WORK, f'{ROCK}_export.glb')


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def world_bounds(objects):
    """Bounds from the vertices (bound_box is stale right after mesh.transform)."""
    pts = np.concatenate([np.array([o.matrix_world @ v.co for v in o.data.vertices]) for o in objects])
    return Vector(pts.min(0)), Vector(pts.max(0))


def import_scan(key, mirror):
    """Import one scan (only its node for a set piece) as one joined mesh object with transforms applied."""
    path, node = scans.SCANS[key]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    keep = [o for o in new if o.type == 'MESH' and (node is None or o.name.startswith(node)
                                                     or o.data.name.startswith(node))]
    for o in new:
        if o not in keep:
            bpy.data.objects.remove(o)
    for o in keep:
        o.parent = None
    bpy.ops.object.select_all(action='DESELECT')
    for o in keep:
        o.select_set(True)
    bpy.context.view_layer.objects.active = keep[0]
    if len(keep) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if mirror:
        obj.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
        obj.data.flip_normals()
    obj.data.update()
    return obj


def ground(obj):
    lo, hi = world_bounds([obj])
    obj.data.transform(Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))))
    obj.data.update()


def decimate_to(obj, target):
    """Collapse-decimate (triangulated) until the triangle count is within the budget."""
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    ratio = target / triangles(obj)
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


to_lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
to_srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)


def save_png(img_name, rgb, colorspace):
    """Write a RES x RES PNG (Blender pixel rows run bottom-up) and return the Blender image."""
    path = os.path.join(TEX, img_name + '.png')
    img = bpy.data.images.get(img_name) or bpy.data.images.new(img_name, RES, RES, alpha=False)
    img.colorspace_settings.name = colorspace
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((RES, RES, 1), np.float32)], 2)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel()); img.filepath_raw = path
    img.file_format = 'PNG'; img.save(); return img


def graded_base():
    """Albedo from the raw bakes: AO folded in, then saturation, linear gain and optional luma contrast."""
    b = to_lin(np.load(os.path.join(WORK, 'bake_base.npy')))
    a = np.load(os.path.join(WORK, 'bake_ao.npy'))
    b = b * (1 - CFG['ao_strength'] * (1 - a))
    g = CFG['grade']
    luma = (b @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    if 'contrast' in g:
        b = b * np.power(np.maximum(luma, 1e-5) / luma.mean(), g['contrast'] - 1)
        luma = (b @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    if 'tint_mix' in g:
        # Optional: replace this fraction of each texel by its luma times the mean tint, which evens out patches of
        # another hue (7rock04's orange lichen face) while keeping the light-dark texture.
        tint = b.reshape(-1, 3).mean(0) / max(float(luma.mean()), 1e-5)
        b = b * (1 - g['tint_mix']) + luma * tint * g['tint_mix']
    if 'luma_cap' in g:
        # Optional: texels brighter than luma_cap x the mean luma (pale lichen caps) are scaled down to that cap.
        cap = g['luma_cap'] * luma.mean()
        b = b * np.minimum(1.0, cap / np.maximum(luma, 1e-5)); luma = np.minimum(luma, cap)
    b = (luma + (b - luma) * g['saturation']) * np.array(g['gain'], np.float32)
    print('BUILD albedo linear mean', [round(float(v), 4) for v in b.reshape(-1, 3).mean(0)])
    return to_srgb(b)


def export(lods):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in lods:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=False, export_skins=False, export_morph=False,
                              export_image_format='AUTO', export_extras=False, export_attributes=False,
                              export_vertex_color='NAME', export_vertex_color_name='Color')
    print('BUILD exported', OUT_GLB, 'tris', [triangles(o) for o in lods])


if REGRADE:
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    lods = sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: len(o.name))
    img = save_png(f'{ROCK}_basecolor', graded_base(), 'sRGB')
    img.reload()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    export(lods)
    sys.exit(0)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
high = import_scan(CFG['source'], CFG.get('mirror', False)); high.name = 'High'
high.data.transform(Matrix.LocRotScale(None, Euler([math.radians(a) for a in CFG.get('rotation_deg', [0, 0, 0])]),
                                       Vector(CFG.get('scale', [1, 1, 1]))))
if 'post_scale' in CFG:                         # scale after the tilt (world axes)
    high.data.transform(Matrix.Diagonal(Vector(CFG['post_scale'])).to_4x4())
ground(high)
if 'height_m' in CFG:
    lo, hi = world_bounds([high])
    # with `sink`, the part above the ground (1 - sink of the scan) is height_m tall
    high.data.transform(Matrix.Scale(CFG['height_m'] / (1 - CFG.get('sink', 0)) / (hi.z - lo.z), 4)); ground(high)
# Optional extra scans joined to the main one: each part is centred on its own bounds, then rotated (degrees), scaled
# (absolute, or `size_m` = its largest extent in metres) and moved to `location` in the grounded main scan's frame.
for part in CFG.get('parts', []):
    piece = import_scan(part['source'], part.get('mirror', False))
    plo, phi = world_bounds([piece])
    piece.data.transform(Matrix.Translation(-(plo + phi) / 2))
    scale = Vector(part.get('scale', [1, 1, 1]))
    if 'size_m' in part:
        scale *= part['size_m'] / max(phi - plo)
    piece.data.transform(Matrix.LocRotScale(Vector(part['location']),
                                            Euler([math.radians(a) for a in part.get('rotation_deg', [0, 0, 0])]),
                                            scale))
    bpy.ops.object.select_all(action='DESELECT'); piece.select_set(True); high.select_set(True)
    bpy.context.view_layer.objects.active = high
    bpy.ops.object.join()
if CFG.get('parts'):
    ground(high)
if 'sink' in CFG:
    # A tilted scan rests on an edge: sink it by this fraction of its height. LOD0 is cut flat at the ground below;
    # the scan itself stays whole for the bake (a cut, hole-filled scan baked blank ARM maps).
    lo, hi = world_bounds([high])
    high.data.transform(Matrix.Translation(Vector((0, 0, -CFG['sink'] * (hi.z - lo.z))))); high.data.update()
lo, hi = world_bounds([high])
print('BUILD high', ROCK, 'tris', triangles(high), 'size', [round(v, 3) for v in hi - lo])
if '--preview' in ARGS:
    # Quick look at the assembled scans (composites) before decimation and baking: work/<rock>/preview.png
    scene.render.engine = 'BLENDER_EEVEE'; scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = 384; scene.eevee.taa_render_samples = 8
    scene.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
    next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND').inputs['Strength'].default_value = 0.9
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.2
    scene.collection.objects.link(sun)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam)
    scene.camera = cam
    yaw, el = math.radians(CFG['review_yaw']), math.radians(CFG.get('review_el', 15))
    sun.rotation_euler = (math.radians(40), 0, yaw - math.radians(35))
    d = Vector((math.sin(yaw) * math.cos(el), -math.cos(yaw) * math.cos(el), math.sin(el)))
    cam.location = (lo + hi) / 2 + d * (hi - lo).length * 1.25
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(WORK, 'preview.png'); bpy.ops.render.render(write_still=True)
    sys.exit(0)

names = [CFG['name']] + [f"{CFG['name']}_LOD{i}" for i in (1, 2, 3)]
lods = []
me = high.data.copy(); bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
if 'sink' in CFG:
    cut = bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), dist=1e-6,
                                 plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_inner=True)
    caps = bmesh.ops.holes_fill(bm, edges=[e for e in cut['geom_cut'] if isinstance(e, bmesh.types.BMEdge)],
                                sides=0)['faces']
    for f in caps:                              # the cap must face down (the dome unwrap seams round it)
        f.normal_update()
        if f.normal.z > 0:
            f.normal_flip()
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
bm.to_mesh(me); bm.free()
lod0 = bpy.data.objects.new(names[0], me); scene.collection.objects.link(lod0)
while lod0.data.uv_layers:
    lod0.data.uv_layers.remove(lod0.data.uv_layers[0])
while lod0.data.color_attributes:
    lod0.data.color_attributes.remove(lod0.data.color_attributes[0])
lod0.data.materials.clear()
if (CFG.get('parts') and CFG.get('fuse', True)) or CFG.get('remesh'):
    # Fuse the joined scans into one closed surface (voxel remesh): the dome unwrap below still finds a single visible
    # island and no triangles go to hidden contact faces; the bake still reads the scans. With fuse false (a cluster
    # of separate stones) the pieces stay separate: collapse never merges them and each gets its own dome seam.
    bpy.ops.object.select_all(action='DESELECT'); lod0.select_set(True); bpy.context.view_layer.objects.active = lod0
    mod = lod0.modifiers.new('Remesh', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = CFG.get('voxel', 0.006)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    print('BUILD remeshed tris', triangles(lod0))
decimate_to(lod0, CFG['targets'][0])
lod0.data.uv_layers.new(name='UVMap')
bpy.ops.object.select_all(action='DESELECT'); lod0.select_set(True); bpy.context.view_layer.objects.active = lod0
# Dome unwrap: per connected piece, one seam round its largest connected underside patch, so each piece's visible
# surface is one island and the LOD collapses never smear texels across island borders (they meet at hidden bases).
bm = bmesh.new(); bm.from_mesh(lod0.data); bm.faces.ensure_lookup_table()
pieces, seen = [], set()
for start in bm.faces:
    if start in seen:
        continue
    piece = {start}; stack = [start]; seen.add(start)
    while stack:
        f = stack.pop()
        for e in f.edges:
            for g in e.link_faces:
                if g not in seen:
                    seen.add(g); piece.add(g); stack.append(g)
    pieces.append(piece)
patch = set()
for piece in pieces:
    zs = [v.co.z for f in piece for v in f.verts]; zmin, zmax = min(zs), max(zs)
    bottom = {f for f in piece if f.normal.z < -0.5 and f.calc_center_median().z < zmin + 0.25 * (zmax - zmin)}
    seeds = sorted(bottom, key=lambda f: f.calc_center_median().z)[:1]
    found = set(seeds); stack = list(seeds)
    while stack:
        f = stack.pop()
        for e in f.edges:
            for g in e.link_faces:
                if g in bottom and g not in found:
                    found.add(g); stack.append(g)
    patch |= found
for e in bm.edges:
    e.seam = len(e.link_faces) == 2 and ((e.link_faces[0] in patch) != (e.link_faces[1] in patch))
bm.to_mesh(lod0.data); bm.free()
print('BUILD pieces', len(pieces))
print('BUILD underside faces', len(patch), 'seam edges', sum(e.use_seam for e in lod0.data.edges))
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.unwrap(method='MINIMUM_STRETCH', margin=0.01)
bpy.ops.uv.pack_islands(rotate=True, margin=0.01)
bpy.ops.object.mode_set(mode='OBJECT')
lods.append(lod0)
for level in (1, 2, 3):
    lod = bpy.data.objects.new(names[level], lod0.data.copy()); scene.collection.objects.link(lod)
    decimate_to(lod, CFG['targets'][level])
    lods.append(lod)
band = CFG.get('ground_band', 0.12)
for lod in lods:
    # Collapse lifts the flat base on the coarser levels; lower each level's bottom band back onto the ground, fading
    # to no change at `band` metres up, so no level floats.
    zmin = min(v.co.z for v in lod.data.vertices)
    for v in lod.data.vertices:
        if v.co.z < band:                       # the lowest vertex lands on 0, the band top stays put
            v.co.z -= zmin * (1 - (v.co.z - zmin) / (band - zmin))
    lod.data.update()
    for p in lod.data.polygons:
        p.use_smooth = True
    print('BUILD lod', lod.name, 'tris', triangles(lod), 'zmin', round(min(v.co.z for v in lod.data.vertices), 4),
          'zmax', round(max(v.co.z for v in lod.data.vertices), 4))

# ---------------------------------------------------------------- bake
scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences


def gpu_free_mib():
    try:
        out = __import__('subprocess').run(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits'],
                                           capture_output=True, text=True, timeout=20).stdout
        return min(int(v) for v in out.split())
    except Exception:
        return 0


# The GPU is shared with other sessions and a failed CUDA context cannot be retried in the same Blender run, so the
# device is chosen before baking: the CPU with ROCK_BAKE_CPU=1 or under 3 GiB of free GPU memory.
use_gpu = os.environ.get('ROCK_BAKE_CPU') != '1' and gpu_free_mib() >= 3072
print('BUILD bake device', 'GPU' if use_gpu else 'CPU')
for kind in ('OPTIX', 'CUDA') if use_gpu else ():
    try:
        prefs.compute_device_type = kind; prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = 'GPU'; break
    except Exception:
        continue
scene.cycles.samples = 16
bake = scene.render.bake
bake.use_selected_to_active = True; bake.cage_extrusion = CFG.get('cage_extrusion', 0.04)
bake.max_ray_distance = CFG.get('max_ray', 0.15)
bake.margin = 16; bake.margin_type = 'EXTEND'
target_mat = bpy.data.materials.new('BakeTarget'); target_mat.use_nodes = True
lod0.data.materials.clear(); lod0.data.materials.append(target_mat)
tnode = target_mat.node_tree.nodes.new('ShaderNodeTexImage'); target_mat.node_tree.nodes.active = tnode
scan_mats = []


def feeding_image(socket):
    """The image texture node that feeds a socket, through any intermediate nodes (glTF imports: Meshy models)."""
    stack = [link.from_node for link in socket.links]
    while stack:
        node = stack.pop()
        if node.type == 'TEX_IMAGE':
            return node
        stack += [link.from_node for inp in node.inputs for link in inp.links]
    return None


for hmat in high.data.materials:
    hnt = hmat.node_tree
    bsdf = next(n for n in hnt.nodes if n.type == 'BSDF_PRINCIPLED')
    images = {os.path.basename(n.image.filepath or n.image.name): n for n in hnt.nodes if n.type == 'TEX_IMAGE' and n.image}
    # Poly Haven scans name their maps _diff_ / _arm_; other models (Meshy) are read by the BSDF links: base colour,
    # and the metallic-roughness image (G roughness, B metal) with no AO channel (AO bakes white).
    diff = next((n for k, n in images.items() if '_diff_' in k), None) or feeding_image(bsdf.inputs['Base Color'])
    arm = next((n for k, n in images.items() if '_arm_' in k), None)
    sep = hnt.nodes.new('ShaderNodeSeparateColor')
    if arm is None:
        mr = feeding_image(bsdf.inputs['Roughness'])
        combine = hnt.nodes.new('ShaderNodeCombineColor')
        mr_sep = hnt.nodes.new('ShaderNodeSeparateColor')
        hnt.links.new(mr.outputs['Color'], mr_sep.inputs['Color'])
        combine.inputs['Red'].default_value = 1.0
        hnt.links.new(mr_sep.outputs['Green'], combine.inputs['Green'])
        hnt.links.new(mr_sep.outputs['Blue'], combine.inputs['Blue'])
        hnt.links.new(combine.outputs['Color'], sep.inputs['Color'])
    else:
        hnt.links.new(arm.outputs['Color'], sep.inputs['Color'])
    scan_mats.append({'tree': hnt, 'out': next(n for n in hnt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output),
                      'bsdf': bsdf, 'diff': diff.outputs['Color'], 'arm': sep})


def bake_map(name, kind, colorspace, source=None):
    img = bpy.data.images.new(name, RES, RES, alpha=False); img.colorspace_settings.name = colorspace
    tnode.image = img
    emits = []
    if source is not None:
        for scan in scan_mats:
            emit = scan['tree'].nodes.new('ShaderNodeEmission')
            scan['tree'].links.new(source(scan), emit.inputs['Color'])
            scan['tree'].links.new(emit.outputs['Emission'], scan['out'].inputs['Surface'])
            emits.append(emit)
    bpy.ops.object.select_all(action='DESELECT'); high.select_set(True); lod0.select_set(True)
    bpy.context.view_layer.objects.active = lod0
    bpy.ops.object.bake(type=kind)
    for scan, emit in zip(scan_mats, emits):
        scan['tree'].links.new(scan['bsdf'].outputs['BSDF'], scan['out'].inputs['Surface'])
        scan['tree'].nodes.remove(emit)
    a = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(a)
    return a.reshape(RES, RES, 4)


normal = bake_map('normal', 'NORMAL', 'Non-Color')
np.save(os.path.join(WORK, 'bake_base.npy'), bake_map('base_raw', 'EMIT', 'sRGB', lambda s: s['diff'])[..., :3])
np.save(os.path.join(WORK, 'bake_ao.npy'), bake_map('ao', 'EMIT', 'Non-Color', lambda s: s['arm'].outputs['Red'])[..., :1])
rough = bake_map('rough', 'EMIT', 'Non-Color', lambda s: s['arm'].outputs['Green'])[..., :1]
metal = bake_map('metal', 'EMIT', 'Non-Color', lambda s: s['arm'].outputs['Blue'])[..., :1]
rough = np.maximum(rough, CFG.get('roughness_min', 0.0))
base_png = save_png(f'{ROCK}_basecolor', graded_base(), 'sRGB')
normal_png = save_png(f'{ROCK}_normal', normal[..., :3], 'Non-Color')
orm_png = save_png(f'{ROCK}_metal_rough', np.concatenate([np.zeros_like(rough), rough, metal], 2), 'Non-Color')

# ---------------------------------------------------------------- COLOR_0, runtime material and export
shade = CFG.get('base_shade', 1.0)
for lod in lods:
    zmax = max(v.co.z for v in lod.data.vertices)
    attr = lod.data.color_attributes.new('Color', 'BYTE_COLOR', 'CORNER')
    for loop in lod.data.loops:
        t = min(1.0, lod.data.vertices[loop.vertex_index].co.z / (0.35 * zmax))
        k = shade + (1 - shade) * t * t * (3 - 2 * t)
        attr.data[loop.index].color = (k, k, k, 1.0)
    lod.data.color_attributes.active_color_name = 'Color'
mat = bpy.data.materials.new(CFG['name']); mat.use_nodes = True
nt = mat.node_tree; pb = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(img):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n


# COLOR_0 is exported by name; the engine multiplies it into the base colour (review_render.py does the same).
nt.links.new(tex(base_png).outputs['Color'], pb.inputs['Base Color'])
nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal_png).outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], pb.inputs['Normal'])
sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(orm_png).outputs['Color'], sp.inputs['Color'])
nt.links.new(sp.outputs['Green'], pb.inputs['Roughness']); nt.links.new(sp.outputs['Blue'], pb.inputs['Metallic'])
for obj in lods:
    obj.data.materials.clear(); obj.data.materials.append(mat)
bpy.data.objects.remove(high, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
export(lods)
