"""MM8 rocks from Poly Haven CC0 scans (rocks_lib.SCANS), settings in rocks.json. Adapted from the MM6 leftover-rock
builder (../../../mm6_dungeons_3d/leftovers/scripts/build_rock.py, read only), with:
- parts: each a scan (`scan` key; set pieces by node) turned so that its survey view `view` (degrees, survey.py) faces
  the front, scaled (`scale`, x/y/z after the turn; a negative x mirrors), optionally rolled (`tilt` [x, y] degrees),
  reshaped into a wedge (`ramp`), and for secondary parts sized (`size`: height as a fraction of the main part's),
  sunk (`sink`, fraction of its height) and moved (`at`, x/y in main-part heights). `share` is a part's share of each
  LOD budget, `drop` the first LOD without it.
- fit (default 1): the assembly's front width/height is pulled toward the sprite's (inventory width/height) by
  scaling x up and z down by the square root of the ratio (fit 0: off).
- One dome unwrap per part (one seam round its underside), packed together; LOD1..3 decimate each part's LOD0.
- Maps baked from the full scans (Cycles, selected to active): normal, diffuse, AO / roughness / metal (ARM; scans
  with only a roughness map get AO 1, metal 0), the scan's position and normal (float) for the moss and tar masks.
- Colour: AO folded in, `grade` (saturation, optional pre-gain `gain`, optional luma `contrast`), `moss` layers (dict
  or list: green where the surface is low, faces up or sits in a crevice, broken by noise; colour "auto" takes the
  sprite's green pixels), then a per-channel gain that brings the visible albedo's linear mean to the sprite's
  (x `lift`, default 1). `match: false` keeps the pre-gain only.
- tar (rock61/62): a glossy black network (3D Voronoi cell borders of the rock's surface, widened in crevices).
  Raised as opaque geometry, material `Tar` (no textures, roughness ~0.2, full specular): each LOD's surface
  subdivided, cut to the tar mask and lifted by a rounded rope profile (tar_mesh). The rock under it is darkened,
  with a flat-plus-bulge normal and the same roughness, so the coarse LOD reads too.
- COLOR_0: vertex occlusion against the parts and the ground (contact shadow) x `tint`.
Texture size `texture_size` (default by height: >= 50 units 1024, >= 25 512, else 256); the metallic-roughness map
is half that. Writes work/<rock>/{textures/*.png, <rock>.blend, <rock>_export.glb}.
Usage: blender --background --python build_rock.py -- <rock>"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rocks_lib as rl  # noqa: E402

pl = rl.pl
PROP = sys.argv[sys.argv.index('--') + 1]
CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rocks.json')))[PROP]
INV = {e['name']: e for e in json.load(open(os.path.join(rl.HERE, '..', 'inventory.json')))}[PROP]
HEIGHT = CFG.get('height', INV['height'])
STONE = CFG.get('stone_height', HEIGHT)          # rune stones: plants rise above the stone to the full height
WIDTH = CFG.get('width', INV['width'])
RES = CFG.get('texture_size', 1024 if HEIGHT >= 50 else 512 if HEIGHT >= 25 else 256)
MR_RES = max(128, RES // 2)
WORK = os.path.join(rl.WORK, PROP); TEX = os.path.join(WORK, 'textures')
os.makedirs(TEX, exist_ok=True)
NAME = CFG.get('name', 'Rock' + PROP[4:])
LEVEL_OF = {}


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def decimate_to(obj, target):
    """Collapse-decimate to the budget (props_lib.decimate_to, but accepting up to 8 % over when collapse stalls)."""
    try:
        return pl.decimate_to(obj, target)
    except RuntimeError:
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
        best = None
        for ratio in np.linspace(target / triangles(obj), 0.2 * target / triangles(obj), 24):
            mod = obj.modifiers.new('Decimate', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
            mod.ratio = float(ratio); mod.use_collapse_triangulate = True
            count = sum(len(p.vertices) - 2 for p in obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.polygons)
            if count <= target * 1.08:
                bpy.ops.object.modifier_apply(modifier=mod.name)
                print('BUILD decimate stalled', obj.name, target, '->', count)
                return count
            obj.modifiers.remove(mod)
        raise


def bounds(objs):
    pts = []
    for o in objs:
        co = np.zeros(len(o.data.vertices) * 3, np.float32); o.data.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3) @ np.array(o.matrix_world.to_3x3()).T + np.array(o.matrix_world.translation)
        pts.append(co)
    pts = np.concatenate(pts)
    return Vector(pts.min(0).tolist()), Vector(pts.max(0).tolist())


def import_part(index, part):
    objs = rl.import_scan(part['scan'])
    for o in objs:                               # keep world transforms when dropping the importer's parents
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = f'High{index}'
    for o in [o for o in bpy.data.objects if o.type != 'MESH']:
        bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for slot in obj.material_slots:              # own material copies, tagged with the part index (moss mask)
        slot.material = slot.material.copy()
        slot.material['part'] = index
    me = obj.data
    me.transform(Matrix.Rotation(math.radians(-part.get('view', 0)), 4, 'Z'))
    tilt = part.get('tilt', [0, 0])               # roll about x / y (degrees) before scaling: stand a slab up
    if tilt != [0, 0]:
        me.transform(Euler((math.radians(tilt[0]), math.radians(tilt[1]), 0)).to_matrix().to_4x4())
    scale = part.get('scale', [1, 1, 1])
    me.transform(Matrix.Diagonal(Vector(list(scale) + [1])))
    if scale[0] * scale[1] * scale[2] < 0:
        me.flip_normals()                        # mirrored scan
    lo, hi = bounds([obj])
    me.transform(Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))))
    ramp = part.get('ramp')
    if ramp:
        # wedge: heights keep their scale up to ramp.start (fraction of the width from the left), then fall linearly
        # to ramp.end x their height at the right edge (ramp.mirror: from the right)
        lo, hi = bounds([obj])
        for v in me.vertices:
            t = (v.co.x - lo.x) / (hi.x - lo.x)
            if ramp.get('mirror'):
                t = 1 - t
            v.co.z *= 1.0 if t <= ramp['start'] else 1.0 + (ramp['end'] - 1.0) * (t - ramp['start']) / (1 - ramp['start'])
        me.update()
    taper = part.get('taper')
    if taper is not None:                        # narrower toward the top (standing stones): top at `taper` x width
        lo, hi = bounds([obj])
        for v in me.vertices:
            k = 1.0 - (1.0 - taper) * v.co.z / hi.z
            v.co.x *= k; v.co.y *= k
        me.update()
    me.update()
    return obj


def place_parts():
    highs = []
    main_height = None
    for index, part in enumerate(CFG['parts']):
        obj = import_part(index, part)
        lo, hi = bounds([obj])
        if main_height is None:
            main_height = hi.z
        elif 'size' in part:
            obj.data.transform(Matrix.Diagonal(Vector((part['size'] * main_height / hi.z,) * 3 + (1,))))
            lo, hi = bounds([obj])
        at = part.get('at', [0, 0])
        obj.data.transform(Matrix.Translation(Vector((at[0] * main_height, at[1] * main_height,
                                                      part.get('lift', 0.0) * main_height
                                                      - part.get('sink', 0.0) * hi.z))))
        obj.data.update()
        highs.append(obj)
    lo, hi = bounds(highs)
    lo.z = max(lo.z, 0.0)
    fit = CFG.get('fit', 1.0)
    if fit:
        ratio = (WIDTH / STONE) / ((hi.x - lo.x) / (hi.z - lo.z))
        sx = ratio ** (0.5 * fit)
        for obj in highs:
            obj.data.transform(Matrix.Diagonal(Vector((sx, 1.0, 1.0 / sx, 1.0))))
            obj.data.update()
        print('BUILD fit ratio', round(ratio, 3), 'x', round(sx, 3), 'z', round(1 / sx, 3))
        lo, hi = bounds(highs); lo.z = max(lo.z, 0.0)
    factor = rl.units(STONE) / (hi.z - lo.z)
    for obj in highs:
        obj.data.transform(Matrix.Diagonal(Vector((factor,) * 3 + (1,))) @
                           Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, 0))))
        obj.data.update()
    return highs


def dome_unwrap(obj):
    """One seam round the largest flat underside patch, so the visible surface is one island."""
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.faces.ensure_lookup_table()
    zmin = min(v.co.z for v in bm.verts); zmax = max(v.co.z for v in bm.verts)
    span = zmax - zmin
    bottom = {f for f in bm.faces if (f.normal.z < -0.3 and f.calc_center_median().z < zmin + 0.3 * span) or
              f.calc_center_median().z < zmin + 0.04 * span}
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
    bm.to_mesh(obj.data); bm.free()
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='MINIMUM_STRETCH', margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')
    overlap = uv_overlap(obj)
    if overlap > 0.02:
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(70), island_margin=0.01)
        bpy.ops.object.mode_set(mode='OBJECT')
        print('BUILD dome overlap', round(overlap, 3), '-> smart project overlap', round(uv_overlap(obj), 3))
    else:
        print('BUILD dome overlap', round(overlap, 3))


def raster(obj, res):
    """Per-texel count of UV triangles covering it (texel row 0 = v 0, as Blender image pixels)."""
    me = obj.data; me.calc_loop_triangles()
    uv = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get('uv', uv)
    uv = uv.reshape(-1, 2) * res
    count = np.zeros((res, res), np.int32)
    for tri in me.loop_triangles:
        p = uv[list(tri.loops)]
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(d) < 1e-12:
            continue
        a = ((p[1, 1] - p[2, 1]) * (xs - p[2, 0]) + (p[2, 0] - p[1, 0]) * (ys - p[2, 1])) / d
        b = ((p[2, 1] - p[0, 1]) * (xs - p[2, 0]) + (p[0, 0] - p[2, 0]) * (ys - p[2, 1])) / d
        inside = (a >= 0) & (b >= 0) & (a + b <= 1)
        count[np.clip(ys[inside].astype(int), 0, res - 1), np.clip(xs[inside].astype(int), 0, res - 1)] += 1
    return count


def uv_overlap(obj, res=256):
    me = obj.data
    uv = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    lo, hi = uv.min(0), uv.max(0)
    saved = uv.copy()
    me.uv_layers.active.data.foreach_set('uv', ((uv - lo) / np.maximum(hi - lo, 1e-6) * 0.999).ravel())
    count = raster(obj, res)
    me.uv_layers.active.data.foreach_set('uv', saved.ravel())
    return float((count > 1).sum() / max((count > 0).sum(), 1))


def low_part(index, high, target):
    me = high.data.copy()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
    # drop loose crumbs (scan fragments): they cannot collapse and would eat the coarse LOD budgets
    seen, islands = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        stack, island = [v], []
        seen.add(v)
        while stack:
            u = stack.pop(); island.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w not in seen:
                    seen.add(w); stack.append(w)
        islands.append(island)
    crumbs = [v for isl in islands if len(isl) < 0.02 * len(bm.verts) for v in isl]
    if crumbs:
        bmesh.ops.delete(bm, geom=crumbs, context='VERTS')
        print('BUILD removed', len(islands) - sum(len(i) >= 0.02 * (len(bm.verts) + len(crumbs)) for i in islands),
              'crumb islands,', len(crumbs), 'vertices')
    bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(f'Low{index}', me); bpy.context.scene.collection.objects.link(obj)
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    obj.data.materials.clear()
    remesh = CFG['parts'][index].get('remesh')
    if remesh:                                   # stretched or noisy scans: a clean voxel surface first
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
        mod = obj.modifiers.new('Remesh', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = remesh * rl.units(HEIGHT)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    decimate_to(obj, target)
    obj.data.uv_layers.new(name='UVMap')
    dome_unwrap(obj)
    return obj


def join(name, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name; obj.data.name = name
    return obj


def ground(obj):
    """Flatten buried vertices onto the ground, then lower the level onto it (decimation lifts a flat base)."""
    for v in obj.data.vertices:
        if v.co.z < 0:
            v.co.z = 0.0
    zmin = min(v.co.z for v in obj.data.vertices)
    for v in obj.data.vertices:
        v.co.z -= zmin
    obj.data.update()


def build_lods(highs):
    targets = CFG['targets']
    shares = [p.get('share', 1.0) for p in CFG['parts']]
    total = sum(shares)
    parts0 = [low_part(i, h, max(12, int(targets[0] * s / total))) for i, (h, s) in enumerate(zip(highs, shares))]
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts0:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts0[0]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True, margin=CFG.get('pack_margin', 0.01 if RES >= 512 else 0.02))
    bpy.ops.object.mode_set(mode='OBJECT')
    lods = []
    for level in range(len(targets)):
        keep = [(i, p) for i, p in enumerate(parts0) if CFG['parts'][i].get('drop', 99) > level]
        share_sum = sum(shares[i] for i, _ in keep)
        pieces = []
        for i, p in keep:
            copy = bpy.data.objects.new(f'L{level}_{i}', p.data.copy()); bpy.context.scene.collection.objects.link(copy)
            if level:
                decimate_to(copy, max(8, int(targets[level] * shares[i] / share_sum)))
            pieces.append(copy)
        obj = join(NAME if level == 0 else f'{NAME}_LOD{level}', pieces)
        for poly in obj.data.polygons:
            poly.use_smooth = True
        ground(obj)
        LEVEL_OF[obj.name] = level
        lods.append(obj)
    for p in parts0:
        bpy.data.objects.remove(p)
    return lods


# ---------------------------------------------------------------- bake
def setup_cycles():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    if not os.environ.get('ROCK_GPU'):           # the GPU is shared with other sessions (out-of-memory bakes)
        scene.cycles.samples = 16
        return scene
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
    return scene


def bake_all(high, lod0, size):
    scene = setup_cycles()
    bake = scene.render.bake
    bake.use_selected_to_active = True
    bake.cage_extrusion = CFG.get('cage', 0.03) * size; bake.max_ray_distance = CFG.get('max_ray', 0.12) * size
    bake.margin = 16 if RES >= 512 else 8; bake.margin_type = 'EXTEND'
    target = bpy.data.materials.new('BakeTarget'); target.use_nodes = True
    lod0.data.materials.clear(); lod0.data.materials.append(target)
    tnode = target.node_tree.nodes.new('ShaderNodeTexImage'); target.node_tree.nodes.active = tnode
    mossy_parts = set()
    for layer in moss_layers():
        mossy_parts |= set(layer.get('parts', [0]))
    scans = []
    for hmat in high.data.materials:
        nt = hmat.node_tree
        images = {os.path.basename(n.image.filepath or n.image.name): n for n in nt.nodes
                  if n.type == 'TEX_IMAGE' and n.image}
        arm = next((n for k, n in images.items() if '_arm_' in k), None)
        rough = next((n for k, n in images.items() if '_rough_' in k), None)
        one = nt.nodes.new('ShaderNodeValue'); one.outputs[0].default_value = 1.0
        zero = nt.nodes.new('ShaderNodeValue'); zero.outputs[0].default_value = 0.0
        if arm is not None:
            sep = nt.nodes.new('ShaderNodeSeparateColor')
            nt.links.new(arm.outputs['Color'], sep.inputs['Color'])
            ao_s, rough_s, metal_s = sep.outputs['Red'], sep.outputs['Green'], sep.outputs['Blue']
        else:
            ao_s, rough_s, metal_s = one.outputs[0], rough.outputs['Color'], zero.outputs[0]
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        part = nt.nodes.new('ShaderNodeValue')
        part.outputs[0].default_value = 1.0 if hmat.get('part', 0) in mossy_parts else 0.0
        scans.append({'tree': nt, 'out': next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output),
                      'bsdf': next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'),
                      'diff': next(n for k, n in images.items() if '_diff_' in k).outputs['Color'],
                      'ao': ao_s, 'rough': rough_s, 'metal': metal_s, 'geo': geo, 'part': part.outputs[0]})

    def bake_map(name, kind, colorspace, source=None, float_buffer=False):
        img = bpy.data.images.new(name, RES, RES, alpha=False, float_buffer=float_buffer)
        img.colorspace_settings.name = colorspace
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
        try:
            bpy.ops.object.bake(type=kind)
        except RuntimeError as error:            # the GPU is shared with other sessions: fall back to the CPU
            print('BUILD bake on CPU after', str(error)[:80])
            bpy.context.scene.cycles.device = 'CPU'
            bpy.ops.object.bake(type=kind)
        for scan, emit in zip(scans, emits):
            scan['tree'].links.new(scan['bsdf'].outputs['BSDF'], scan['out'].inputs['Surface'])
            scan['tree'].nodes.remove(emit)
        a = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(a)
        return a.reshape(RES, RES, 4)[..., :3]

    maps = {
        'normal': bake_map('normal', 'NORMAL', 'Non-Color'),
        'base': bake_map('base_raw', 'EMIT', 'sRGB', lambda s: s['diff']),
        'ao': bake_map('ao', 'EMIT', 'Non-Color', lambda s: s['ao'])[..., 0],
        'rough': bake_map('rough', 'EMIT', 'Non-Color', lambda s: s['rough'])[..., 0],
        'metal': bake_map('metal', 'EMIT', 'Non-Color', lambda s: s['metal'])[..., 0],
        'pos': bake_map('pos', 'EMIT', 'Non-Color', lambda s: s['geo'].outputs['Position'], True),
        'nrm': bake_map('nrm', 'EMIT', 'Non-Color', lambda s: s['geo'].outputs['Normal'], True),
        'mossy': bake_map('mossy', 'EMIT', 'Non-Color', lambda s: s['part'])[..., 0],
    }
    return maps


# ---------------------------------------------------------------- colour
def to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def noise3(pos, scale, seed):
    rng = np.random.default_rng(seed)
    out = np.zeros(pos.shape[:-1], np.float32)
    for _ in range(8):
        k = rng.normal(size=3) * scale; ph = rng.uniform(0, 2 * math.pi)
        out += np.sin(pos @ k + ph)
    return out / 8 * 0.5 + 0.5


def lattice_noise(p, seed):
    """Trilinear value noise on the unit lattice (p: ... x 3), values 0..1."""
    rng = np.random.default_rng(seed)
    table = rng.uniform(size=4096).astype(np.float32)
    i = np.floor(p).astype(np.int64); f = p - i
    f = f * f * (3 - 2 * f)
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                h = ((i[..., 0] + dx) * 73856093 ^ (i[..., 1] + dy) * 19349663 ^ (i[..., 2] + dz) * 83492791) & 4095
                wgt = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * \
                    (f[..., 2] if dz else 1 - f[..., 2])
                out = out + table[h] * wgt
    return out


def fbm(p, freq, octaves, seed):
    """Fractal value noise, roughly 0..1 with mean 0.5."""
    out, amp, total = 0.0, 1.0, 0.0
    for o in range(octaves):
        out = out + lattice_noise(p * freq * 2 ** o + o * 17.3, seed + o) * amp
        total += amp; amp *= 0.5
    return out / total


def green_mask(px):
    return (px[:, 1] > px[:, 0] * 1.04) & (px[:, 1] > px[:, 2] * 1.25)


def sprite_green(px):
    """The sprite's moss pixels, linear, sorted by luma."""
    g = to_lin(px[green_mask(px)])
    return g[np.argsort(g @ LUMA)]


def moss_layers():
    moss = CFG.get('moss')
    return [] if not moss else moss if isinstance(moss, list) else [moss]


def sprite_pixels():
    """Opaque pixels (sRGB 0..1) of the native x2 sprite."""
    img = bpy.data.images.load(rl.sprite_path(INV['files'][0]), check_existing=False)
    a = np.empty(img.size[0] * img.size[1] * 4, np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    a = a.reshape(-1, 4)
    return a[a[:, 3] > 0.5, :3]


def save(name, rgb, res, alpha=None, colorspace='sRGB'):
    img = bpy.data.images.new(name, res, res, alpha=alpha is not None)
    if rgb.shape[0] != res:
        rgb = resample(rgb, res)
    a = np.ones((res, res, 1), np.float32) if alpha is None else alpha[..., None]
    img.pixels.foreach_set(np.concatenate([np.clip(rgb, 0, 1), a], 2).astype(np.float32).ravel())
    img.filepath_raw = os.path.join(TEX, name + '.png'); img.file_format = 'PNG'; img.save()
    img.colorspace_settings.name = colorspace
    return img


def resample(rgb, res):
    k = rgb.shape[0] // res
    return rgb.reshape(res, k, res, k, -1).mean((1, 3))


def voronoi_edges(pos, cells, seed):
    """Distance (in units of the cell size) to the nearest border between 3D Voronoi cells of `cells` random seeds
    spread over the rock's bounds; pos is N x 3 in rock heights."""
    rng = np.random.default_rng(seed)
    lo, hi = pos.min(0), pos.max(0)
    seeds = lo + rng.uniform(size=(cells, 3)) * (hi - lo)
    cell = float(np.cbrt(np.prod(hi - lo) / cells))
    out = np.empty(len(pos), np.float32)
    for s in range(0, len(pos), 65536):
        p = pos[s:s + 65536]
        d = np.linalg.norm(p[:, None, :] - seeds[None], axis=2)
        d.sort(1)
        out[s:s + 65536] = (d[:, 1] - d[:, 0]) / cell
    return out


def blur(a, radius):
    """Separable box blur (three passes ~ Gaussian) of a 2D array, radius in texels."""
    r = max(1, int(radius))
    for _ in range(3):
        for axis in (0, 1):
            c = np.cumsum(np.pad(a, [(r + 1, r) if ax == axis else (0, 0) for ax in range(2)], mode='edge'), axis)
            a = (np.take(c, range(2 * r + 1, c.shape[axis]), axis) - np.take(c, range(0, c.shape[axis] - 2 * r - 1), axis)) / (2 * r + 1)
    return a


def height_normal(normal, h, strength):
    """Add a height field's slope (per texel, UV space) to a tangent-space normal map (0..1 encoded)."""
    n = normal * 2 - 1
    dx = np.gradient(h, axis=1) * strength; dy = np.gradient(h, axis=0) * strength
    n = n + np.stack([-dx, -dy, np.zeros_like(h)], -1) * n[..., 2:3]
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def palette_transfer(b, visible, sprite, tr):
    """Bring the scan's albedo (linear) toward the sprite's tonal range and palette: each texel's luma is mapped
    through the scan->sprite luma quantiles (visible texels; the sprite's spread scaled by `contrast` about its
    median, since part of it is painted light and shadow), and its chroma blended (`palette`) toward the sprite's
    mean chroma at the same quantile. Green (moss) pixels of the sprite are left out when the rock has moss.
    `amount` blends the whole result with the input."""
    s = to_lin(sprite)
    if moss_layers():
        s = s[~green_mask(sprite)]
    if CFG.get('tar'):
        s = s[s @ LUMA > 0.03]                   # the tar's black pixels
    ls = s @ LUMA
    order = np.argsort(ls); s, ls = s[order], ls[order]
    lb = b @ LUMA
    q = np.linspace(0, 1, 33)
    src_q = np.quantile(lb[visible], q)
    dst_q = np.quantile(ls, q)
    mid = np.median(ls)
    dst_q = mid * np.power(np.maximum(dst_q, 1e-5) / mid, tr.get('contrast', 0.6))
    src_q = np.maximum.accumulate(src_q + np.arange(33) * 1e-7)
    lt = np.interp(lb, src_q, dst_q)
    # sprite chroma (colour / luma) per quantile bin, looked up by the texel's quantile
    bins = np.array_split(np.arange(len(ls)), 32)
    chroma = np.array([s[i].mean(0) / max(float(ls[i].mean()), 1e-5) for i in bins], np.float32)
    rank = np.interp(lb, src_q, q)
    k = np.clip((rank * 32).astype(int), 0, 31)
    own = b / np.maximum(lb, 1e-5)[..., None]
    p = tr.get('palette', 0.6)
    out = lt[..., None] * (own * (1 - p) + chroma[k] * p)
    a = tr.get('amount', 1.0)
    return b * (1 - a) + out * a


BOX = {}                                         # stone front bounds (x0, x1, z top), set before the bake


def sprite_to_model(px, py):
    """Sprite x2 pixel (canvas coordinates, y down) -> model (x, z), through CFG sprite_box [x0, x1, ytop, ybottom],
    the sprite pixels that the stone's front bounds cover."""
    x0, x1, yt, yb = CFG['sprite_box']
    return (BOX['x0'] + (px - x0) / (x1 - x0) * (BOX['x1'] - BOX['x0']), (yb - py) / (yb - yt) * BOX['z1'])


def rune_mask(pos, nrm, runes):
    """Carved strokes taken from the sprite (textures/runes_<rock>.png, scripts/make_runes.py, covering sprite_box),
    projected from the front onto the texels that face it."""
    img = bpy.data.images.load(os.path.join(rl.HERE, 'textures', f'runes_{PROP}.png'), check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a); a = a.reshape(h, w, 4)[..., 0]
    bpy.data.images.remove(img)
    x0, x1, yt, yb = CFG['sprite_box']
    u = (pos[..., 0] - BOX['x0']) / (BOX['x1'] - BOX['x0'])
    v = pos[..., 2] / BOX['z1']                  # image rows from the bottom (Blender pixel order)
    ix = np.clip((u * (w - 1)).astype(int), 0, w - 1); iy = np.clip((v * (h - 1)).astype(int), 0, h - 1)
    inside = (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
    facing = np.clip((-nrm[..., 1] - 0.15) / 0.35, 0, 1)
    return a[iy, ix] * inside * facing


def sprite_rgba():
    img = bpy.data.images.load(rl.sprite_path(INV['files'][0]), check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1]               # image rows top-down


def native_profile(nat):
    """The sprite's prerendered lighting as median luminance (sRGB grey) per (surface elevation, height) bin, after
    level_generation/creatures/claude_shared/native_shading.py (read only). Each opaque pixel's elevation comes from a
    half-ellipsoid fitted to the silhouette (half width x half width x height): top pixels face up, rim pixels face
    sideways. The 2-px silhouette rim (the painted outline) and moss, plant and tar pixels are left out.
    Returns (profile 2D table, elevation bins, height bins, sorted palette pixels sRGB)."""
    px = sprite_rgba()
    alpha = px[..., 3] > 0.5
    rows, cols = np.nonzero(alpha)
    top, bottom = rows.min(), rows.max(); left, right = cols.min(), cols.max()
    cx = (left + right) / 2; a = max((right - left) / 2, 1); c = max(bottom - top, 1)
    inner = alpha.copy()
    for _ in range(2):                            # drop the outline ring
        inner[1:-1, 1:-1] &= inner[:-2, 1:-1] & inner[2:, 1:-1] & inner[1:-1, :-2] & inner[1:-1, 2:]
    rgb = px[..., :3]
    keep = inner.copy()
    if moss_layers() or CFG.get('plants'):
        keep &= ~((rgb[..., 1] > rgb[..., 0] * 1.04) & (rgb[..., 1] > rgb[..., 2] * 1.25))
    lum = (to_lin(rgb) @ LUMA)
    if CFG.get('tar'):
        keep &= lum > 0.03
    rr, cc = np.nonzero(keep)
    x = (cc - cx) / a; z = (bottom - rr) / c
    y = np.sqrt(np.clip(1 - x * x - z * z, 0.02, 1))
    n = np.stack([x / a, y / a, z / c], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    elev = np.degrees(np.arcsin(np.clip(n[:, 2], -1, 1)))
    hgt = z
    grey = to_srgb(lum[rr, cc])
    eb = np.linspace(0, 90, nat.get('elevation_bins', 7)); hb = np.linspace(0, 1, nat.get('height_bins', 5))
    table = np.zeros((len(hb), len(eb)), np.float32)
    ei = np.clip(np.round(elev / 90 * (len(eb) - 1)).astype(int), 0, len(eb) - 1)
    hi_ = np.clip(np.round(hgt * (len(hb) - 1)).astype(int), 0, len(hb) - 1)
    overall = float(np.median(grey))
    for j in range(len(hb)):
        for i in range(len(eb)):
            sel = (hi_ == j) & (ei == i)
            if sel.sum() >= 12:
                table[j, i] = np.median(grey[sel])
            else:                                  # sparse bin: the elevation column, then the height row
                col = ei == i; row = hi_ == j
                table[j, i] = np.median(grey[col]) if col.sum() >= 12 else (np.median(grey[row]) if row.sum() else overall)
    palette = rgb[rr, cc]
    palette = palette[np.argsort(to_lin(palette) @ LUMA)]
    print('BUILD native profile height x elevation\n' + '\n'.join(
        f'  h{hb[j]:.2f} ' + ' '.join(f'{v:.2f}' for v in table[j]) for j in range(len(hb))))
    return table, eb, hb, palette


def lookup2(table, eb, hb, elev, hgt):
    """Bilinear lookup of the profile table at texel elevations (degrees) and heights (0..1)."""
    fe = np.clip(elev / 90 * (len(eb) - 1), 0, len(eb) - 1.001); fh = np.clip(hgt * (len(hb) - 1), 0, len(hb) - 1.001)
    e0, h0 = fe.astype(int), fh.astype(int); te, th = fe - e0, fh - h0
    return (table[h0, e0] * (1 - te) * (1 - th) + table[h0, e0 + 1] * te * (1 - th) +
            table[h0 + 1, e0] * (1 - te) * th + table[h0 + 1, e0 + 1] * te * th)


def native_shade(b, maps, height, nat):
    """Base colour (linear) carrying the sprite's lighting and palette:
    grey = native profile(smoothed facing, height), compressed toward its mean by `contrast` (the engine lights it
    again), times the scan's local detail (luma high-pass) ^ `detail`, times cavity AO ^ `cavity`, plus a faint bright
    line on convex edges (`edge`); then coloured by luminance through the sprite's own pixels (median of the pixels
    nearest each luminance) with a saturation boost `chroma`."""
    table, eb, hb, palette = native_profile(nat)
    nrm = maps['nrm'] / np.maximum(np.linalg.norm(maps['nrm'], axis=-1, keepdims=True), 1e-6)
    smooth = np.stack([blur(nrm[..., k], RES / nat.get('facing_blur', 40)) for k in range(3)], -1)
    smooth /= np.maximum(np.linalg.norm(smooth, axis=-1, keepdims=True), 1e-6)
    elev = np.degrees(np.arcsin(np.clip(smooth[..., 2], -1, 1)))
    hgt = np.clip(maps['pos'][..., 2] / height, 0, 1)
    target = lookup2(table, eb, hb, elev, hgt)
    mean = float(np.median(table))
    target = mean + (target - mean) * nat.get('contrast', 0.9)
    luma = b @ LUMA
    # local detail, log-compressed so a scan's big albedo patches do not turn black or white (rock05)
    ratio = np.log(np.clip(luma / np.maximum(blur(luma, RES / 40), 1e-4), 1e-3, 1e3))
    detail = np.exp(0.45 * np.tanh(ratio * nat.get('detail', 1.3) / 0.45))
    cavity = np.clip(maps['ao'], 0.05, 1) ** nat.get('cavity', 1.2)
    n = maps['normal'] * 2 - 1                     # convex edges: divergence of the tangent-space normal
    div = blur(np.gradient(n[..., 0], axis=1) + np.gradient(n[..., 1], axis=0), max(1, RES / 512))
    edge = 1 + nat.get('edge', 0.12) * np.clip(div * RES / 64, 0, 1)
    grey = np.clip(target * detail * edge, 0, min(1.0, float(table.max()) * 1.2))   # no brighter than the sprite
    grey_lin = to_lin(grey) * cavity
    grey = to_srgb(grey_lin)
    # colour by luminance through the sprite's pixels: 48 stops, each the median of its nearest pixels
    plum = to_srgb(to_lin(palette) @ LUMA)
    stops = np.linspace(0, 1, 48)
    chroma_stops = []
    for s in stops:
        k = np.searchsorted(plum, s); half = max(len(palette) // 60, 6)
        win = palette[max(0, min(k, len(palette) - 1) - half):min(len(palette), k + half + 1)]
        col = np.median(win, 0); l = max(float(to_srgb(to_lin(col) @ LUMA)), 1e-3)
        chroma_stops.append(col / l)
    chroma_stops = np.array(chroma_stops)
    ch = np.stack([np.interp(grey, stops, chroma_stops[:, k]) for k in range(3)], -1)
    col = grey[..., None] * ch
    col = grey[..., None] + (col - grey[..., None]) * nat.get('chroma', 1.3)
    print('BUILD native median grey', round(mean, 3), 'texel grey p5/p50/p95',
          [round(float(v), 3) for v in np.percentile(grey, [5, 50, 95])])
    return to_lin(np.clip(col, 0, 1))


def project_detail(final, maps, lod0, proj):
    """The sprite's own painted surface pattern (cracks, veins) projected onto the texels that see the sprite's
    camera: front (yaw 0, which `view` turned toward the sprite), `elevation` degrees above. The model's projected
    outline is framed onto the sprite's opaque box, so the pattern lands where the sprite paints it. Projected is the
    per-channel high-pass of the x2 sprite (colour over its alpha-normalised blur, so orange veins keep their hue and
    the silhouette outline adds nothing), as a multiplier on the linear colour, so the baked low-frequency shading
    stays. Weight: facing toward the camera (smoothed normals), fading to 0 toward the sides; the back gets the mirror
    image at `back` strength."""
    e = math.radians(proj.get('elevation', 8.0))
    up = np.array([0.0, math.sin(e), math.cos(e)], np.float32)        # screen up of a camera at -y, tilted down
    co = np.array([v.co[:] for v in lod0.data.vertices], np.float32)
    sx_v, sy_v = co[:, 0], co @ up
    px = sprite_rgba()
    a = px[..., 3]
    rows, cols = np.nonzero(a > 0.5)
    top, bottom, left, right = rows.min(), rows.max(), cols.min(), cols.max()
    rgb = to_lin(px[..., :3])
    # band-pass: the restored sprite carries fine dither speckle; smooth it away first so the painted cracks and
    # veins (a few pixels wide) are what remains
    pre = proj.get('pre_blur', 0)
    if pre:
        rgb = np.stack([blur(rgb[..., k] * a, pre) for k in range(3)], -1) / np.maximum(blur(a, pre), 1e-3)[..., None]
    sigma = proj.get('sigma', 3.0)
    soft = np.stack([blur(rgb[..., k] * a, sigma) for k in range(3)], -1) / np.maximum(blur(a, sigma), 1e-3)[..., None]
    ratio = np.clip(rgb / np.maximum(soft, 1e-4), 0.35, 2.5)
    inner = a > 0.5
    for _ in range(3):                           # keep away from the painted outline
        inner[1:-1, 1:-1] &= inner[:-2, 1:-1] & inner[2:, 1:-1] & inner[1:-1, :-2] & inner[1:-1, 2:]
    ratio = np.where(inner[..., None], ratio, 1.0)
    pos = maps['pos']
    nrm = maps['nrm'] / np.maximum(np.linalg.norm(maps['nrm'], axis=-1, keepdims=True), 1e-6)
    sm = np.stack([blur(nrm[..., k], RES / 128) for k in range(3)], -1)
    sm /= np.maximum(np.linalg.norm(sm, axis=-1, keepdims=True), 1e-6)
    view = np.array([0.0, -math.cos(e), math.sin(e)], np.float32)     # toward the camera
    out = final.copy()
    for sign, strength in ((1.0, proj.get('strength', 1.0)), (-1.0, proj.get('back', 0.5))):
        if strength <= 0:
            continue
        v = view * np.array([1, sign, 1], np.float32)
        u_ = up * np.array([1, sign, 1], np.float32)
        facing = sm @ v
        # everything the camera sees counts (a low dome's top faces it at only a few degrees), full from ~15 degrees
        w = np.clip((facing - 0.02) / proj.get('fade', 0.25), 0, 1) * strength
        sx = pos[..., 0]; sy = pos @ u_
        syv = co @ u_
        col = left + (sx - sx_v.min()) / (sx_v.max() - sx_v.min()) * (right - left)
        row = bottom - (sy - syv.min()) / (syv.max() - syv.min()) * (bottom - top)
        col = np.clip(col, 0, a.shape[1] - 1.001); row = np.clip(row, 0, a.shape[0] - 1.001)
        c0, r0 = col.astype(int), row.astype(int); fc, fr = (col - c0)[..., None], (row - r0)[..., None]
        r = (ratio[r0, c0] * (1 - fc) * (1 - fr) + ratio[r0, c0 + 1] * fc * (1 - fr) +
             ratio[r0 + 1, c0] * (1 - fc) * fr + ratio[r0 + 1, c0 + 1] * fc * fr)   # bilinear
        out = out * np.power(r, w[..., None])
        print('BUILD projected', 'front' if sign > 0 else 'back', 'texels', int((w > 0.05).sum()))
    return out


def textures(maps, lod0, height):
    maps['ao'] = np.where(maps['ao'] < 0.08, 1.0, maps['ao'])   # scans with zero-AO islands (nb05)
    b = to_lin(maps['base'])
    b = b * (1 - CFG.get('ao_strength', 0.7) * (1 - maps['ao'][..., None]))
    luma = (b @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    g = CFG.get('grade', {})
    if 'contrast' in g:
        b = b * np.power(np.maximum(luma, 1e-5) / luma.mean(), g['contrast'] - 1)
        luma = (b @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    b = (luma + (b - luma) * g.get('saturation', 0.6)) * np.array(g.get('gain', [1, 1, 1]), np.float32)
    pos, nrm = maps['pos'], maps['nrm']
    covered = raster(lod0, RES) > 0
    visible = covered & (nrm[..., 2] > -0.3)
    sprite = sprite_pixels()
    native = CFG.get('native', {}) if CFG.get('native', {}) is not False else None
    if native is not None:                       # 2026-10-16 default: the sprite's lighting and palette baked in
        b = native_shade(b, maps, height, native)
    else:                                        # earlier route: palette transfer, then a mean-colour gain
        tr = CFG.get('transfer', {})
        if tr.get('amount', 1.0) > 0:
            b = palette_transfer(b, visible, sprite, tr)
    m_total = np.zeros(b.shape[:2], np.float32); tone_sum = np.zeros_like(b)
    greens = sprite_green(sprite)
    for i, moss in enumerate(moss_layers()):
        z = pos[..., 2] / height
        line = moss.get('height', 0.0) * (0.4 + 1.2 * fbm(pos / height, 2.5, 2, 6 + 10 * i))
        low = np.clip((line - z) / (max(moss.get('height', 0.0), 1e-3) * 0.5), 0, 1)
        up = np.clip((nrm[..., 2] - 0.35) / 0.4, 0, 1) * moss.get('up', 0.0)
        crevice = np.clip((0.88 - maps['ao']) / 0.3, 0, 1) * moss.get('crevice', 0.0)
        f = moss.get('freq', 10.0)
        n = fbm(pos / height, f, 3, 7 + 10 * i)
        m = np.clip((np.maximum(low, np.maximum(up, crevice)) + (n - 0.5) * 2.4 - moss.get('bias', 0.25)) * 2.5, 0, 1)
        # speckled edges: fine clumps break the patch borders up, as the sprites' painted moss
        fine = fbm(pos / height, f * 6, 2, 9 + 10 * i)
        m = m * np.clip((fine - (1 - m) * moss.get('speckle', 0.7)) * 3 + 0.3, 0, 1)
        m *= moss.get('amount', 1.0) * maps['mossy']
        colour = moss['colour']
        clump = fbm(pos / height, moss.get('clump_freq', 30.0), 3, 11 + 10 * i)
        if colour == 'auto' and len(greens) > 20:
            # tone and hue from the sprite's own moss pixels (sorted by luma), picked by a fine clump noise
            flat = clump.ravel(); rank = np.empty(flat.size, np.float32)
            rank[np.argsort(flat)] = np.linspace(0, 0.999, flat.size)      # uniform ranks: the full tonal range
            rank = rank.reshape(clump.shape)
            tone = greens[(rank * len(greens)).astype(int)] * moss.get('gain', 1.0)
            print('BUILD moss sprite colour sRGB', [int(round(v)) for v in to_srgb(greens.mean(0)) * 255],
                  'pixels', len(greens))
        else:
            c = to_lin(np.array(colour if colour != 'auto' else [92, 107, 40], np.float32) / 255)
            tone = c * (0.6 + 0.8 * clump[..., None])
        m = m * (1 - m_total)                    # later layers fill what earlier ones left
        tone_sum += tone * m[..., None]; m_total += m
        print('BUILD moss layer', i, 'coverage', round(float(m[visible].mean()), 3))
    rough = np.maximum(maps['rough'], CFG.get('roughness_min', 0.0))
    normal = maps['normal']
    tar = CFG.get('tar')
    t_mask = t_height = None
    if tar:
        # glossy black network: borders of 3D Voronoi cells (width varies with noise) plus crevices
        p = pos.reshape(-1, 3) / height
        edge = voronoi_edges(p, tar['cells'], tar.get('seed', 3)).reshape(RES, RES)
        width = tar['width'] * (0.55 + 0.9 * noise3(pos / height, tar.get('width_freq', 4.0), 21))
        t = np.clip((width - edge) / (0.35 * tar['width']), 0, 1)
        t = np.maximum(t, np.clip((tar.get('crevice_ao', 0.0) - maps['ao']) / 0.15, 0, 1))
        t *= np.clip((nrm[..., 2] + 0.6) / 0.4, 0, 1)                # none on the underside
        t_mask = np.clip(blur(t, RES / 512) * 1.6 - 0.3, 0, 1)
        # rounded rope profile across each flow (0 at the edge, 1 along its middle), smooth so it carries no grain
        t_height = np.clip(blur(t_mask, RES / 192) * 1.4 - 0.2, 0, 1) ** 0.5 * (t_mask > 0.02)
        dark = np.clip(blur(t_mask, RES / 256) * 1.8, 0, 1)[..., None]
        # under the tar the scan's grain would sparkle at low roughness: a flat normal plus the smooth bulge
        flat = np.broadcast_to(np.array([0.5, 0.5, 1.0], np.float32), normal.shape)
        normal = normal * (1 - dark) + flat * dark
        normal = height_normal(normal, blur(t_height, RES / 256), tar.get('bulge', 3.0) * RES / 1024)
        tar_lin = to_lin(np.array(tar.get('colour', [14, 12, 12]), np.float32) / 255)
        # the ropes carry the gloss; the darkened rock under and around them stays matte (no grazing sheen)
        rough = rough * (1 - dark[..., 0]) + tar.get('under_roughness', 0.55) * dark[..., 0]
        print('BUILD tar coverage', round(float(t_mask[visible].mean()), 3))
    w = visible.astype(np.float32)[..., None]
    rock_w = w * (1 - m_total[..., None])
    rock_part = b
    fixed = tone_sum
    if tar:
        rock_w = rock_w * (1 - dark)
    # the rock's visible texels (moss and tar left out) take the mean sRGB of the sprite's rock pixels (its moss
    # and tar pixels left out) x lift; solved in linear, refined because sRGB means and linear gains do not commute
    rock_px = sprite
    if moss_layers():
        rock_px = rock_px[~green_mask(rock_px)]
    if tar:
        rock_px = rock_px[rock_px @ LUMA > 0.16]
    target = rock_px.mean(0) * CFG.get('lift', 1.0)
    gain = np.ones(3, np.float32)
    if CFG.get('match', native is None):         # the native profile already carries the sprite's brightness
        for _ in range(8):
            got = (to_srgb(b * gain) * rock_w).sum((0, 1)) / rock_w.sum()
            gain = np.clip(gain * to_lin(target) / np.maximum(to_lin(got), 1e-5), 0.05, 20.0)
            if native is not None:               # after native shading only a level correction, never a re-flatten
                gain = np.clip(gain, 0.6, 1.4)
    rock_part = b * (1 - m_total[..., None])
    if tar:
        rock_part = rock_part * (1 - dark); fixed = fixed * (1 - dark) + tar_lin * dark
    final = rock_part * gain + fixed
    mean = (to_srgb(final) * w).sum((0, 1)) / w.sum()
    print('BUILD gain', [round(float(v), 3) for v in gain], 'albedo mean sRGB',
          [int(round(v)) for v in mean * 255], 'sprite mean sRGB', [int(round(v)) for v in sprite.mean(0) * 255],
          'rock target', [int(round(v)) for v in target * 255])
    proj = CFG.get('project')
    if proj:
        final = project_detail(final, maps, lod0, proj)
    runes = CFG.get('runes')
    if runes:
        mask = rune_mask(pos, nrm, runes)
        final = final * (1 - runes.get('dark', 0.7) * mask[..., None])
        normal = height_normal(normal, -blur(mask, RES / 1024), runes.get('relief', 3.0) * RES / 1024)
        rough = np.maximum(rough, mask * 0.9)
        print('BUILD runes coverage', round(float(mask[visible].mean()), 4))
    srgb = to_srgb(final)
    lo, hi = np.percentile(srgb[visible] * 255, 1), np.percentile(srgb[visible] * 255, 99)
    print('BUILD basecolor sRGB p1/p99', round(float(lo)), round(float(hi)))
    stem = f'mm8_{PROP}'
    imgs = {'base': save(f'{stem}_basecolor', srgb, RES),
            'normal': save(f'{stem}_normal', normal, RES, colorspace='Non-Color'),
            'mr': save(f'{stem}_mr', np.stack([np.zeros_like(rough), rough, maps['metal']], -1), MR_RES,
                       colorspace='Non-Color')}
    return imgs, (t_mask, pos, nrm, covered) if tar else None


def runtime_material(name, imgs, alpha=False):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(img):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
    base = tex(imgs['base'])
    nt.links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
    if alpha:
        nt.links.new(base.outputs['Alpha'], bsdf.inputs['Alpha'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(imgs['normal']).outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(imgs['mr']).outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


def tar_material(tar):
    """Opaque glossy black, no textures: smooth geometry gives the broad soft highlight along each rope."""
    mat = bpy.data.materials.new('Tar'); mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    c = to_lin(np.array(tar.get('colour', [14, 12, 12]), np.float32) / 255)
    bsdf.inputs['Base Color'].default_value = (float(c[0]), float(c[1]), float(c[2]), 1.0)
    bsdf.inputs['Roughness'].default_value = tar.get('roughness', 0.2)
    bsdf.inputs['Metallic'].default_value = 0.0
    return mat


def thin(mask):
    """Zhang-Suen thinning of a boolean image to one-pixel centre lines."""
    m = np.pad(mask.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            p2, p3, p4 = m[:-2, 1:-1], m[:-2, 2:], m[1:-1, 2:]
            p5, p6, p7 = m[2:, 2:], m[2:, 1:-1], m[2:, :-2]
            p8, p9 = m[1:-1, :-2], m[:-2, :-2]
            ring = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            count = sum(r.astype(np.int32) for r in ring[:8])
            trans = sum(((ring[k] == 0) & (ring[k + 1] == 1)).astype(np.int32) for k in range(8))
            c = m[1:-1, 1:-1] == 1
            if step == 0:
                kill = c & (count >= 2) & (count <= 6) & (trans == 1) & (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                kill = c & (count >= 2) & (count <= 6) & (trans == 1) & (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            if kill.any():
                m[1:-1, 1:-1][kill] = 0; changed = True
        if not changed:
            return m[1:-1, 1:-1].astype(bool)


def erosion_depth(mask, limit=40):
    """Per pixel: how many 4-neighbour erosions it survives (half the local width, in pixels)."""
    depth = np.zeros(mask.shape, np.float32); cur = mask.copy()
    for k in range(limit):
        if not cur.any():
            break
        depth += cur
        nb = np.pad(cur, 1)
        cur = cur & nb[:-2, 1:-1] & nb[2:, 1:-1] & nb[1:-1, :-2] & nb[1:-1, 2:]
    return depth


def trace(skel):
    """Polylines (lists of (row, col)) between junctions and ends of a one-pixel skeleton."""
    pts = set(zip(*np.nonzero(skel)))
    nbrs = {p: [(p[0] + dy, p[1] + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                if (dy or dx) and (p[0] + dy, p[1] + dx) in pts] for p in pts}
    nodes = {p for p in pts if len(nbrs[p]) != 2}
    seen_edges = set(); lines = []
    for start in list(nodes) + list(pts):
        for nxt in nbrs[start]:
            if (start, nxt) in seen_edges:
                continue
            line = [start]; prev, cur = start, nxt
            seen_edges.add((start, nxt)); seen_edges.add((nxt, start))
            while True:
                line.append(cur)
                if cur in nodes or cur == start:
                    break
                ahead = [q for q in nbrs[cur] if q != prev and (cur, q) not in seen_edges]
                if not ahead:
                    break
                seen_edges.add((cur, ahead[0])); seen_edges.add((ahead[0], cur))
                prev, cur = cur, ahead[0]
            if len(line) > 1:
                lines.append(line)
    return lines


def tar_ropes(fields, tar, height):
    """Rope network of the tar: centre lines of the tar mask (UV space; the dome unwrap keeps the visible surface on
    one island) lifted to 3D through the baked position and normal maps. Returns [(points, normals, radii)]."""
    t_mask, pos, nrm, covered = fields
    k = max(1, t_mask.shape[0] // 512)            # work at 512
    m = blur(t_mask.reshape(512, k, 512, k).mean((1, 3)), 2) > 0.5      # smooth outline: fewer skeleton spurs
    cov = covered.reshape(512, k, 512, k).any((1, 3))
    m &= cov
    depth = erosion_depth(m)
    skel = thin(m) & (depth >= 2)
    P = pos.reshape(512, k, 512, k, 3)[:, 0, :, 0]; N = nrm.reshape(512, k, 512, k, 3)[:, 0, :, 0]
    ropes = []
    ends = {p for p in zip(*np.nonzero(skel))
            if sum(skel[p[0] + dy, p[1] + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                   if (dy or dx) and 0 <= p[0] + dy < 512 and 0 <= p[1] + dx < 512) == 1}
    for line in trace(skel):
        pts = [Vector(P[r, c]) for r, c in line]
        nos = [Vector(N[r, c]).normalized() for r, c in line]
        # radius: the local half width in pixels, converted to metres through the 3D length of a pixel step
        steps = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
        px = sum(steps) / max(len(steps), 1) / 1.2
        rad = [depth[r, c] * px for r, c in line]
        length = sum(steps)
        spur = line[0] in ends or line[-1] in ends
        if length < height * tar.get('min_rope', 0.04) or (spur and length < 4 * max(rad)):
            continue                                 # crumbs and thinning spurs
        ropes.append((pts, nos, rad))
    return ropes


def tar_mesh(obj, level, fields, tar, height):
    """Raised tar on one LOD: smooth half-tubes along the rope network (tar_ropes), each sunk a little into the
    rock, swollen where it is wide and tapered at free ends; opaque, smooth shaded, material `Tar`. Coarser levels
    sample the ropes more sparsely with fewer sides; the budget sets the sampling step."""
    budget = tar['targets'][level]
    if not budget:
        return
    ropes = ROPES.setdefault('ropes', tar_ropes(fields, tar, height))
    sides = (6, 4, 3, 2)[level]
    tris_per_seg = 2 * sides

    def length(rope):
        return sum((rope[0][i + 1] - rope[0][i]).length for i in range(len(rope[0]) - 1))
    # coarser levels keep the longest ropes only; then the sampling step that fits the budget
    keep = min(int(len(ropes) * (1.0, 0.7, 0.45, 0.25)[level]), budget // (2 * tris_per_seg))
    ropes = sorted(ropes, key=length, reverse=True)[:max(1, keep)]   # at least two segments per rope fit
    step = height * 0.01
    while sum(max(1, int(round(length(r) / step))) for r in ropes) * tris_per_seg > budget:
        step *= 1.08
    bm = bmesh.new()
    lift = tar.get('lift', 0.8)
    for pts, nos, rad in ropes:
        # resample along the 3D length
        acc = [0.0]
        for i in range(len(pts) - 1):
            acc.append(acc[-1] + (pts[i + 1] - pts[i]).length)
        n_seg = max(1, int(round(acc[-1] / step)))
        samples = []
        for j in range(n_seg + 1):
            d = acc[-1] * j / n_seg
            i = min(max(np.searchsorted(acc, d) - 1, 0), len(pts) - 2)
            t = (d - acc[i]) / max(acc[i + 1] - acc[i], 1e-9)
            samples.append((pts[i].lerp(pts[i + 1], t), nos[i].lerp(nos[i + 1], t).normalized(),
                            rad[i] + (rad[i + 1] - rad[i]) * t))
        rings = []
        phase = (len(pts) * 0.7) % 6.28
        for j, (p, n, r) in enumerate(samples):
            a = samples[min(j + 1, len(samples) - 1)][0] - samples[max(j - 1, 0)][0]
            tangent = (a - n * a.dot(n)).normalized() if a.length > 1e-9 else Vector((1, 0, 0))
            side = n.cross(tangent).normalized()
            r = max(r, height * 0.012) * tar.get('rope_scale', 1.5)
            # a gentle wave sideways (the sprites' ropes meander), none at the rope ends so junctions still meet
            d = acc[-1] * j / n_seg
            p = p + side * r * 0.45 * math.sin(2 * math.pi * d / (7 * r) + phase) * math.sin(math.pi * j / n_seg)
            if samples and (j == 0 or j == len(samples) - 1) and len(samples) > 2:
                r *= 0.85
            ring = []
            for q in range(sides + 1):                # half tube from one side over the top to the other
                ang = math.pi * (-0.08 + 1.16 * q / sides)
                ring.append(bm.verts.new(p - n * r * 0.3 + side * r * math.cos(ang) + n * r * lift * math.sin(ang)))
            rings.append(ring)
        for j, (ra, rb) in enumerate(zip(rings, rings[1:])):
            axis = samples[j][0] - samples[j][1] * max(samples[j][2], height * 0.012) * 0.3
            for q in range(sides):
                f = bm.faces.new((ra[q], ra[q + 1], rb[q + 1], rb[q]))
                f.normal_update()
                if f.normal.dot(f.calc_center_median() - axis) < 0:   # outward, away from the rope's axis
                    f.normal_flip()
    for v in bm.verts:                           # ropes over buried stone parts stay on the ground
        v.co.z = max(v.co.z, 0.0)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    for f in bm.faces:
        f.material_index = 1; f.smooth = True
    me = bpy.data.meshes.new('tar')
    for m in obj.data.materials:
        me.materials.append(m)
    bm.to_mesh(me); bm.free()
    part = bpy.data.objects.new('tar', me); bpy.context.scene.collection.objects.link(part)
    print('BUILD tar ropes', obj.name, 'ropes', len(ropes), 'tris', triangles(part), 'step', round(step, 4))
    bpy.ops.object.select_all(action='DESELECT'); part.select_set(True); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()


ROPES = {}


def colour(obj, size):
    pl.vertex_occlusion(obj, rays=(48, 32, 20, 12)[min(3, LEVEL_OF[obj.name])], distance=0.2 * size,
                        strength=CFG.get('contact_strength', 0.35), floor=True)
    tint = CFG.get('tint', [1, 1, 1])
    attr = obj.data.color_attributes['Color']
    for item in attr.data:
        c = item.color
        item.color = (c[0] * tint[0], c[1] * tint[1], c[2] * tint[2], 1.0)


pl.reset()
highs = place_parts()
lods = build_lods(highs)
high = join('High', highs)
lo, hi = bounds([high])
size = max(hi - lo)
print('BUILD high', PROP, 'tris', triangles(high), 'size m', [round(v, 3) for v in hi - lo], 'texture', RES)
BOX.update(x0=lo.x, x1=hi.x, z1=hi.z)
maps = bake_all(high, lods[0], size)
imgs, tar_fields = textures(maps, lods[0], hi.z)
mat = runtime_material(NAME, imgs)
tar_mat = tar_material(CFG['tar']) if CFG.get('tar') else None
bpy.data.objects.remove(high, do_unlink=True)
for obj in lods:
    obj.data.materials.clear(); obj.data.materials.append(mat)
    if CFG.get('plants'):
        import plants
        plants.add(obj, LEVEL_OF[obj.name], CFG, sprite_to_model, rl.units)
    if tar_mat is not None:
        obj.data.materials.append(tar_mat)
        tar_mesh(obj, LEVEL_OF[obj.name], tar_fields, CFG['tar'], hi.z)
    colour(obj, size)
    print('LEVEL', LEVEL_OF[obj.name], obj.name, 'tris', triangles(obj), 'zmin',
          round(min(v.co.z for v in obj.data.vertices), 4), 'zmax', round(max(v.co.z for v in obj.data.vertices), 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{PROP}.blend'))
pl.export(lods, os.path.join(WORK, f'{PROP}_export.glb'))
