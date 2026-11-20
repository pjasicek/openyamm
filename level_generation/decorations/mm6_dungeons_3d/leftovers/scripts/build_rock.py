"""Leftover MM6 dungeon rocks (`rock01`..`rock11` p336 sprites and `6rock02`) from Poly Haven CC0 scans (the outdoor
rock sources, read only; rock_common.SCANS), settings in rocks.json:
- parts: each a scan turned by `yaw`, scaled (`scale`, world x/y/z after the yaw), centred on its own footprint,
  stood on the ground, rolled by `tilt` degrees about x/y, sized (`size`: height as a fraction of the main rock's),
  sunk by `sink` (fraction of its height) and moved to `at` (x, y in main-rock heights); the first part is the main
  rock, the rest pebbles. `ramp` reshapes a part into a wedge (heights falling to the right). A part's `yaw` is minus the survey yaw whose view it should show from the front. `share` is the part's share
  of each LOD budget, `drop` the first LOD level without it.
- The assembly is scaled uniformly so its height is the binding height in metres (units / 81.7) and centred on its
  footprint; every low-poly vertex below the ground is flattened onto it (buried pebble bottoms).
- Each part's LOD0 is its own scan collapse-decimated with a dome unwrap (one seam round its underside), the parts
  packed into one atlas; LOD1..3 decimate each part's LOD0 (they keep its UVs) and join.
- Maps baked from the full scans in Cycles (selected to active): normal, diffuse, AO / roughness / metal (ARM), and
  the scan's position and normal (float) for the moss mask. AO folds into the base colour, then `grade` (saturation,
  linear gain, optional luma contrast) and `moss` (green where the surface is low, faces up or sits in a crevice,
  broken by noise; only on the parts listed in `moss.parts`, default the main rock) bring it to the sprite. COLOR_0 is vertex occlusion against the parts and the ground (contact
  shadow between pebbles and rock) times `tint`.
Writes textures/rock_<prop>_{basecolor,normal,mr}.png, work/rocks/<prop>.blend and work/rocks/<prop>_export.glb.
Usage: blender --background --python build_rock.py -- <prop>"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leftovers_lib as ll  # noqa: E402
import rock_common as rc  # noqa: E402

pl = ll.pl
PROP = sys.argv[sys.argv.index('--') + 1]
CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rocks.json')))[PROP]
RES = CFG.get('texture_size', 1024)
WORK = os.path.join(ll.WORK, 'rocks'); os.makedirs(WORK, exist_ok=True)
NAME = CFG['name']


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def bounds(objs):
    """World bounds from the vertices (bound_box is stale right after a mesh transform)."""
    pts = []
    for o in objs:
        co = np.zeros(len(o.data.vertices) * 3, np.float32); o.data.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3) @ np.array(o.matrix_world.to_3x3()).T + np.array(o.matrix_world.translation)
        pts.append(co)
    pts = np.concatenate(pts)
    return Vector(pts.min(0).tolist()), Vector(pts.max(0).tolist())


def import_part(index, part):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=rc.SCANS[part['scan']])
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = f'High{index}'
    for o in [o for o in bpy.data.objects if o not in before and o is not obj]:
        if o.type != 'MESH':
            bpy.data.objects.remove(o)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.parent = None
    for slot in obj.material_slots:              # own material copies, tagged with the part index (moss mask)
        slot.material = slot.material.copy()
        slot.material['part'] = index
    me = obj.data
    me.transform(Matrix.Rotation(math.radians(part.get('yaw', 0)), 4, 'Z'))
    me.transform(Matrix.Diagonal(Vector(part.get('scale', [1, 1, 1]) + [1])))
    if Matrix.Diagonal(Vector(part.get('scale', [1, 1, 1]))).determinant() < 0:
        me.flip_normals()                        # mirrored scan
    lo, hi = bounds([obj])
    me.transform(Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))))
    ramp = part.get('ramp')
    if ramp:
        # wedge: heights keep their scale up to ramp.start (fraction of the width from the left), then fall
        # linearly to ramp.end x their height at the right edge
        lo, hi = bounds([obj])
        for v in me.vertices:
            t = (v.co.x - lo.x) / (hi.x - lo.x)
            v.co.z *= 1.0 if t <= ramp['start'] else 1.0 + (ramp['end'] - 1.0) * (t - ramp['start']) / (1 - ramp['start'])
        me.update()
    tilt = part.get('tilt', [0, 0])
    if tilt != [0, 0]:
        me.transform(Euler((math.radians(tilt[0]), math.radians(tilt[1]), 0)).to_matrix().to_4x4())
        lo, hi = bounds([obj])
        me.transform(Matrix.Translation(Vector((0, 0, -lo.z))))
    return obj


def place_parts():
    """Import and place every part; returns the high objects (main first)."""
    highs = []
    main_height = None
    for index, part in enumerate(CFG['parts']):
        obj = import_part(index, part)
        lo, hi = bounds([obj])
        if main_height is None:
            main_height = hi.z
        elif 'size' in part:                     # pebbles: height as a fraction of the main rock's
            obj.data.transform(Matrix.Diagonal(Vector((part['size'] * main_height / hi.z,) * 3 + (1,))))
            lo, hi = bounds([obj])
        at = part.get('at', [0, 0])
        obj.data.transform(Matrix.Translation(Vector((at[0] * main_height, at[1] * main_height,
                                                      -part.get('sink', 0.0) * hi.z))))
        obj.data.update()
        highs.append(obj)
    lo, hi = bounds(highs)
    lo.z = max(lo.z, 0.0)
    factor = ll.units(CFG['height']) / (hi.z - lo.z)
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
        # a near-closed dome folds over itself: fall back to angle-limited islands
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(70), island_margin=0.01)
        bpy.ops.object.mode_set(mode='OBJECT')
        print('BUILD dome overlap', round(overlap, 3), '-> smart project overlap', round(uv_overlap(obj), 3))
    else:
        print('BUILD dome overlap', round(overlap, 3))


def uv_overlap(obj, res=256):
    """Fraction of covered texels that more than one triangle covers (folded unwraps)."""
    me = obj.data; me.calc_loop_triangles()
    uv = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    lo, hi = uv.min(0), uv.max(0); uv = (uv - lo) / np.maximum(hi - lo, 1e-6) * (res - 1)
    count = np.zeros((res, res), np.int32)
    for tri in me.loop_triangles:
        p = uv[list(tri.loops)]
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(d) < 1e-9:
            continue
        a = ((p[1, 1] - p[2, 1]) * (xs - p[2, 0]) + (p[2, 0] - p[1, 0]) * (ys - p[2, 1])) / d
        b = ((p[2, 1] - p[0, 1]) * (xs - p[2, 0]) + (p[0, 0] - p[2, 0]) * (ys - p[2, 1])) / d
        inside = (a >= 0) & (b >= 0) & (a + b <= 1)
        count[np.clip(ys[inside].astype(int), 0, res - 1), np.clip(xs[inside].astype(int), 0, res - 1)] += 1
    covered = (count > 0).sum()
    return float((count > 1).sum() / max(covered, 1))


def low_part(index, high, target):
    me = high.data.copy()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
    bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(f'Low{index}', me); bpy.context.scene.collection.objects.link(obj)
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    obj.data.materials.clear()
    pl.decimate_to(obj, target)
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
    """Flatten buried vertices onto the ground, then lower the level so its lowest point is on it (decimation can
    lift a flat base a little)."""
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
    # one atlas for all parts: multi-object edit mode packs their islands together
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts0:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts0[0]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()          # texel density by 3D area across the parts
    bpy.ops.uv.pack_islands(rotate=True, margin=0.01)
    bpy.ops.object.mode_set(mode='OBJECT')
    lods = []
    for level in range(len(targets)):
        keep = [(i, p) for i, p in enumerate(parts0) if CFG['parts'][i].get('drop', 99) > level]
        share_sum = sum(shares[i] for i, _ in keep)
        pieces = []
        for i, p in keep:
            copy = bpy.data.objects.new(f'L{level}_{i}', p.data.copy()); bpy.context.scene.collection.objects.link(copy)
            if level:
                pl.decimate_to(copy, max(8, int(targets[level] * shares[i] / share_sum)))
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


LEVEL_OF = {}


# ---------------------------------------------------------------- bake
def setup_cycles():
    scene = bpy.context.scene
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
    return scene


def bake_all(high, lod0, size):
    scene = setup_cycles()
    bake = scene.render.bake
    bake.use_selected_to_active = True
    bake.cage_extrusion = 0.03 * size; bake.max_ray_distance = 0.12 * size
    bake.margin = 16; bake.margin_type = 'EXTEND'
    target = bpy.data.materials.new('BakeTarget'); target.use_nodes = True
    lod0.data.materials.clear(); lod0.data.materials.append(target)
    tnode = target.node_tree.nodes.new('ShaderNodeTexImage'); target.node_tree.nodes.active = tnode
    scans = []
    for hmat in high.data.materials:
        nt = hmat.node_tree
        images = {os.path.basename(n.image.filepath or n.image.name): n for n in nt.nodes
                  if n.type == 'TEX_IMAGE' and n.image}
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(next(n for k, n in images.items() if '_arm_' in k).outputs['Color'], sep.inputs['Color'])
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        part = nt.nodes.new('ShaderNodeRGB'); index = hmat.get('part', 0)
        part.outputs[0].default_value = (1.0 if index in CFG.get('moss', {}).get('parts', [0]) else 0.0, 0, 0, 1)
        scans.append({'tree': nt, 'out': next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output),
                      'bsdf': next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'),
                      'diff': next(n for k, n in images.items() if '_diff_' in k).outputs['Color'], 'arm': sep,
                      'geo': geo, 'part': part})

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
        bpy.ops.object.bake(type=kind)
        for scan, emit in zip(scans, emits):
            scan['tree'].links.new(scan['bsdf'].outputs['BSDF'], scan['out'].inputs['Surface'])
            scan['tree'].nodes.remove(emit)
        a = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(a)
        return a.reshape(RES, RES, 4)[..., :3]

    maps = {
        'normal': bake_map('normal', 'NORMAL', 'Non-Color'),
        'base': bake_map('base_raw', 'EMIT', 'sRGB', lambda s: s['diff']),
        'ao': bake_map('ao', 'EMIT', 'Non-Color', lambda s: s['arm'].outputs['Red'])[..., 0],
        'rough': bake_map('rough', 'EMIT', 'Non-Color', lambda s: s['arm'].outputs['Green'])[..., 0],
        'metal': bake_map('metal', 'EMIT', 'Non-Color', lambda s: s['arm'].outputs['Blue'])[..., 0],
    }
    if CFG.get('moss'):
        maps['pos'] = bake_map('pos', 'EMIT', 'Non-Color', lambda s: s['geo'].outputs['Position'], True)
        maps['nrm'] = bake_map('nrm', 'EMIT', 'Non-Color', lambda s: s['geo'].outputs['Normal'], True)
        maps['mossy'] = bake_map('mossy', 'EMIT', 'Non-Color', lambda s: s['part'].outputs[0])[..., 0]
    return maps


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


def save(name, rgb):
    img = bpy.data.images.new(name, RES, RES, alpha=False)
    img.pixels.foreach_set(np.concatenate([np.clip(rgb, 0, 1), np.ones((RES, RES, 1), np.float32)], 2).ravel())
    img.filepath_raw = os.path.join(ll.TEXTURES, name + '.png'); img.file_format = 'PNG'; img.save()
    return img


def textures(maps, height):
    # some scans' ARM maps hold zero red (no AO) over whole UV islands (namaqualand_boulder_05): no occlusion there
    maps['ao'] = np.where(maps['ao'] < 0.08, 1.0, maps['ao'])
    b = to_lin(maps['base'])
    if os.environ.get('ROCK_DEBUG'):
        save(f'debug_{PROP}_ao', np.repeat(maps['ao'][..., None], 3, -1)); save(f'debug_{PROP}_raw', maps['base'])
    b = b * (1 - CFG['ao_strength'] * (1 - maps['ao'][..., None]))
    luma = (b @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    g = CFG['grade']
    if 'contrast' in g:
        b = b * np.power(np.maximum(luma, 1e-5) / luma.mean(), g['contrast'] - 1)
        luma = (b @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    b = (luma + (b - luma) * g['saturation']) * np.array(g['gain'], np.float32)
    moss = CFG.get('moss')
    if moss:
        pos, nrm = maps['pos'], maps['nrm']
        z = pos[..., 2] / height
        # the skirt's top line wanders between 0.4 and 1.4 x moss.height round the rock
        line = moss['height'] * (0.4 + noise3(pos / height, 3.0, 6))
        low = np.clip((line - z) / (moss['height'] * 0.5), 0, 1)
        up = np.clip((nrm[..., 2] - 0.35) / 0.4, 0, 1) * moss.get('up', 0.0)
        crevice = np.clip((0.88 - maps['ao']) / 0.3, 0, 1) * moss.get('crevice', 0.0)
        n = noise3(pos / height, 9.0, 7) * 0.65 + noise3(pos / height, 30.0, 8) * 0.35
        m = np.clip((np.maximum(low, np.maximum(up, crevice)) + (n - 0.5) * 2.2 - 0.25) * 2.5, 0, 1)
        m *= moss.get('amount', 1.0) * maps['mossy']
        detail = np.clip(luma / max(float(luma.mean()), 1e-4), 0.35, 1.8) ** 0.8
        tone = to_lin(np.array(moss['colour'], np.float32) / 255) * detail
        speck = noise3(pos / height, 80.0, 9)[..., None]
        tone = tone * (0.75 + 0.5 * speck)
        b = b * (1 - m[..., None]) + tone * m[..., None]
        print('BUILD moss coverage', round(float(m.mean()), 3))
    rough = np.maximum(maps['rough'], CFG.get('roughness_min', 0.0))
    imgs = {'base': save(f'rock_{PROP}_basecolor', to_srgb(b)),
            'normal': save(f'rock_{PROP}_normal', maps['normal']),
            'mr': save(f'rock_{PROP}_mr', np.stack([np.zeros_like(rough), rough, maps['metal']], -1))}
    imgs['normal'].colorspace_settings.name = 'Non-Color'; imgs['mr'].colorspace_settings.name = 'Non-Color'
    print('BUILD albedo linear mean', [round(float(v), 4) for v in b.reshape(-1, 3).mean(0)])
    return imgs


def runtime_material(imgs):
    mat = bpy.data.materials.new(NAME); mat.use_nodes = True
    nt = mat.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def tex(img):
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n
    nt.links.new(tex(imgs['base']).outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(imgs['normal']).outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(imgs['mr']).outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    return mat


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
print('BUILD high', PROP, 'tris', triangles(high), 'size m', [round(v, 3) for v in hi - lo])
maps = bake_all(high, lods[0], size)
imgs = textures(maps, hi.z)
mat = runtime_material(imgs)
bpy.data.objects.remove(high, do_unlink=True)
for obj in lods:
    obj.data.materials.clear(); obj.data.materials.append(mat)
    colour(obj, size)
    print('LEVEL', LEVEL_OF[obj.name], obj.name, 'tris', triangles(obj), 'zmin',
          round(min(v.co.z for v in obj.data.vertices), 4), 'zmax', round(max(v.co.z for v in obj.data.vertices), 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{PROP}.blend'))
pl.export(lods, os.path.join(WORK, f'{PROP}_export.glb'))
