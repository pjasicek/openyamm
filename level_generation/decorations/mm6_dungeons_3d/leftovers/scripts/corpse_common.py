"""Shared corpse building for the leftover dungeon corpses, copied from the outdoor
../../../mm6_new_sorpigal_3d/props/scripts/build_corpse.py (read only there) without its CORPSES table: an MM6
peasant (assets_dev/worlds/mm6/models/mm6_p*.glb, read only) posed with world-space bone operations
(corpse_pose.py), baked static and welded, recoloured and bloodied (corpse_texture.py), optional stakes, decimated
per LOD with vertex occlusion in COLOR_0. Everything is written to this batch folder (leftovers_lib.redirect):
textures/<corpse>_{basecolor,normal,mr}.png, work/<corpse>.blend and work/<corpse>_export.glb.
Each build script defines its own table and calls build(name, spec) / preview(name, spec); spec keys as in the
outdoor script ('model', 'rotation', 'hips', 'pose', 'stakes', 'impale', 'wounds', 'texture', 'keep', 'stumps',
'levels') plus 'extra': callable(level, mats, arm_info) -> [objects] for props (ropes, chains, hooks, poles), built
from data captured before the armature is removed ('capture': callable(arm) -> info)."""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leftovers_lib as ll
import corpse_pose as cp
import corpse_texture as ct

pl = ll.pl
MODELS = ll.MODELS
SUPINE_LEFT = Matrix.Rotation(math.radians(90), 3, 'Z') @ Matrix.Rotation(math.radians(-90), 3, 'X')
PRONE_RIGHT = Matrix.Rotation(math.radians(90), 3, 'Z') @ Matrix.Rotation(math.radians(90), 3, 'X')
LEG_BONES = tuple(f'mixamorig:{side}{part}' for side in ('Left', 'Right')
                  for part in ('UpLeg', 'Leg', 'Foot', 'ToeBase'))


def roll(degrees):
    return Matrix.Rotation(math.radians(degrees), 3, 'X')


def stake_preview(name, base, tip, radius, mat):
    return pl.tube(name, base, tip, radius, radius * 0.15, 8, mat, caps=True)


def preview(name, spec):
    pl.reset()
    arm, body = cp.load(os.path.join(MODELS, spec['model']))
    cp.place(arm, spec['rotation'], spec['hips'])
    cp.pose(arm, spec['pose'])
    baked = cp.bake(arm, body, name, drop_groups=('Knife',), keep_groups=spec.get('keep'))
    lines = spec.get('stakes', []) + impale(arm, spec.get('impale', []))
    info = spec['capture'](arm) if 'capture' in spec else None
    if 'post' in spec:
        spec['post'](baked, arm, info)
    bpy.data.objects.remove(body); bpy.data.objects.remove(arm)
    wood = bpy.data.materials.new('Stake'); wood.diffuse_color = (0.3, 0.1, 0.05, 1)
    stakes = [stake_preview(f'stake{i}', *s, wood) for i, s in enumerate(lines)]
    if 'extra' in spec:
        mats = {k: wood for k in ['Stake', 'Flesh'] + list(spec.get('materials', {}))}
        stakes += spec['extra'](0, mats, info)
    lo, hi = pl.bounds([baked] + stakes)
    print('BOUNDS', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
    out = os.path.join(ll.REVIEW, name); os.makedirs(out, exist_ok=True)
    pl.setup_render((512, 512))
    ground = pl.box('ground', (0, 0, -0.01), (3, 3, 0.02))
    paths = pl.render_views([baked] + stakes, out, 'pose', views=((0, 6), (40, 20), (90, 6), (180, 10)))
    print('PREVIEW', paths)


LEVELS = (4600, 1900, 700, 220)      # body triangles per LOD
STAKE_SIDES = (7, 5, 4, 3)


def stake(name, base, tip, radius, sides, mat, seed):
    """Sharpened stake: a slightly tapering pole, then a long point (v = 0 at the ground to 1 at the tip, like the
    `stake` texture), the top ring a little off-centre so the points are not machine-perfect."""
    base, tip = Vector(base), Vector(tip)
    axis = tip - base; length = axis.length; axis.normalize()
    side = axis.orthogonal().normalized(); other = axis.cross(side)
    rings = [(0.0, radius), (0.72, radius * 0.88), (0.86, radius * 0.55), (1.0, 0.0)]
    if sides <= 4:
        rings = [(0.0, radius), (0.76, radius * 0.8), (1.0, 0.0)]
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    grid = []
    for k, (t, r) in enumerate(rings):
        centre = base + axis * (t * length)
        if 0 < t < 1:
            centre += side * (0.15 * radius * math.sin(seed * 2.3 + k))
        if r == 0:
            grid.append([bm.verts.new(centre)] * (sides + 1)); continue
        row = [bm.verts.new(centre + (side * math.cos(2 * math.pi * s / sides + seed) +
                                      other * math.sin(2 * math.pi * s / sides + seed)) * r) for s in range(sides)]
        grid.append(row + [row[0]])
    for k in range(len(rings) - 1):
        for s in range(sides):
            quad = [grid[k][s], grid[k][s + 1], grid[k + 1][s + 1], grid[k + 1][s]]
            coords = [((s) / sides, rings[k][0]), ((s + 1) / sides, rings[k][0]), ((s + 1) / sides, rings[k + 1][0]),
                      (s / sides, rings[k + 1][0])]
            if quad[2] is quad[3]:
                quad = quad[:3]; coords = coords[:2] + [((s + 0.5) / sides, 1.0)]
            f = bm.faces.new(quad)
            for loop, c in zip(f.loops, coords):
                loop[uv].uv = c
    bm.normal_update()
    return pl.to_object(name, bm, mat)


def stake_wounds(body, stakes):
    """Where each stake line enters and leaves the body."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(body, depsgraph)
    wounds = []
    for base, tip, radius in stakes:
        for start, end in ((Vector(base), Vector(tip)), (Vector(tip), Vector(base))):
            direction = (end - start); length = direction.length; direction.normalize()
            hit = bvh.ray_cast(start, direction, length)
            if hit[0] is not None:
                wounds.append((tuple(hit[0]), 0.07, 0.3))
    return wounds


def impale(arm, entries):
    """(bone, t, direction, tip height, radius) -> a stake along the direction through that point of the posed bone,
    from the ground (z = 0) up to the tip height."""
    out = []
    for name, t, direction, top, radius in entries:
        pb = arm.pose.bones[name]
        point = (arm.matrix_world @ pb.head).lerp(arm.matrix_world @ pb.tail, t)
        d = Vector(direction).normalized()
        out.append((tuple(point - d * (point.z / d.z)), tuple(point + d * ((top - point.z) / d.z)), radius))
    return out


def bone_wounds(arm, entries):
    """(bone, t along head -> tail (or -> the head of a named tip bone), radius, run) -> world wounds."""
    out = []
    for entry in entries:
        pb = arm.pose.bones[entry[0]]
        head = arm.matrix_world @ pb.head
        tail = arm.matrix_world @ (arm.pose.bones[entry[4]].head if len(entry) > 4 else pb.tail)
        out.append((tuple(head.lerp(tail, entry[1])), entry[2], entry[3]))
    return out


def stump_cuts(arm, entries):
    """(thigh bone, t) -> (side prefix, plane point, normal pointing down the limb) on the posed armature."""
    out = []
    for name, t in entries:
        pb = arm.pose.bones[name]
        head, tail = arm.matrix_world @ pb.head, arm.matrix_world @ pb.tail
        out.append((name.split(':')[1].split('Up')[0], head.lerp(tail, t), (tail - head).normalized()))
    return out


def seal_stumps(obj, spec, flesh, cuts):
    """Severed limbs: cut each limb square across at its plane, dropping the hip side and any tunic cloth (region
    mask or green texels) still weighted to it, and cap the cut in the Flesh material (the solid blood near the
    stake texture's tip)."""
    images = glb_images(os.path.join(MODELS, spec['model']))
    arrays = {}
    for key in ('region_mask', 'basecolor'):
        path = os.path.join(pl.TEX, '_stump_tmp.png')
        with open(path, 'wb') as f:
            f.write(next(v for k, v in images.items() if key in k))
        arrays[key] = image_array(bpy.data.images.load(path)); os.remove(path)
    mask = arrays['region_mask'][..., 0] > 0.5
    rgb = arrays['basecolor'][..., :3]
    green = (rgb[..., 1] > rgb[..., 0] * 1.08) & (rgb[..., 1] > rgb[..., 2] * 1.15)
    drop_texel = mask | green
    h, w = mask.shape
    bones = cp.strongest_bone(obj)
    obj.data.materials.append(flesh)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.active
    bm.verts.ensure_lookup_table()
    cloth = []
    for f in bm.faces:
        u = sum(l[uv].uv.x for l in f.loops) / len(f.loops); v = sum(l[uv].uv.y for l in f.loops) / len(f.loops)
        if drop_texel[min(h - 1, max(0, int(v * h))), min(w - 1, max(0, int(u * w)))]:
            cloth.append(f)
    side_of = {v: bones[v.index] for v in bm.verts}
    # faces bridging the two limbs (the crotch) would stretch between the separated pieces
    for f in bm.faces:
        sides = {side_of[v].split(':')[-1][:4] for v in f.verts}
        if len(sides) > 1:
            cloth.append(f)
    bm.faces.index_update()
    bmesh.ops.delete(bm, geom=sorted(set(cloth), key=lambda f: f.index), context='FACES')
    caps = []
    for side, point, normal in cuts:
        verts = [v for v in bm.verts if side_of.get(v, '').startswith(f'mixamorig:{side}')]
        bm.verts.index_update(); bm.edges.index_update(); bm.faces.index_update()
        faces = sorted({f for v in verts for f in v.link_faces}, key=lambda f: f.index)
        edges_in = sorted({e for f in faces for e in f.edges}, key=lambda e: e.index)
        geom = verts + edges_in + faces           # ordered: rebuilds give identical bytes
        result = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=point, plane_no=normal, clear_inner=True)
        edges = [e for e in result['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        existing = set(bm.faces)
        bmesh.ops.holes_fill(bm, edges=edges, sides=0)
        new = [f for f in bm.faces if f not in existing]
        bmesh.ops.triangulate(bm, faces=new)
        caps += [f for f in bm.faces if f not in existing]
    # stray scraps the cuts left behind: islands of fewer than 40 faces
    seen = set(); scraps = []
    for f in bm.faces:
        if f in seen:
            continue
        island, stack = [], [f]; seen.add(f)
        while stack:
            g = stack.pop(); island.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in seen:
                        seen.add(h); stack.append(h)
        if len(island) < 40:
            scraps += island
    bmesh.ops.delete(bm, geom=scraps, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    caps = [f for f in caps if f.is_valid]
    for f in caps:
        if f.is_valid:
            f.material_index = 1
            for l in f.loops:
                l[uv].uv = (0.5, 0.96)
    bm.to_mesh(obj.data); bm.free()
    print('STUMPS', 'cloth faces dropped', len(cloth), 'cap faces', len(caps), 'scrap faces', len(scraps))


def image_array(image):
    w, h = image.size
    px = np.zeros(w * h * 4, np.float32); image.pixels.foreach_get(px)
    return px.reshape(h, w, 4)


def save_array(path, rgb_srgb):
    h, w = rgb_srgb.shape[:2]
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    px = np.dstack([np.clip(rgb_srgb, 0, 1), np.ones((h, w))]).astype(np.float32)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path; img.file_format = 'PNG'; img.save()


def glb_images(path):
    """{image name: PNG bytes} of a GLB's embedded images (the region mask is not wired to any imported node)."""
    import json, struct
    data = open(path, 'rb').read()
    length = struct.unpack('<I', data[12:16])[0]
    document = json.loads(data[20:20 + length]); binary = 20 + length + 8
    out = {}
    for image in document['images']:
        view = document['bufferViews'][image['bufferView']]
        start = binary + view.get('byteOffset', 0)
        out[image['name']] = data[start:start + view['byteLength']]
    return out


def texture(name, spec, body, wounds):
    """Writes textures/<name>_basecolor.png (recoloured, bloodied) and unchanged copies of the peasant's normal and
    metal/roughness atlases as <name>_normal.png / <name>_mr.png."""
    images = glb_images(os.path.join(MODELS, spec['model']))
    paths = {}
    for key, suffix in (('basecolor', 'source'), ('normal', 'normal'), ('metal_rough', 'mr'),
                        ('region_mask', 'mask')):
        blob = next(v for k, v in images.items() if key in k)
        paths[suffix] = os.path.join(pl.TEX, f'{name}_{suffix}.png')
        with open(paths[suffix], 'wb') as f:
            f.write(blob)
    base = bpy.data.images.load(paths['source']); mask_image = bpy.data.images.load(paths['mask'])
    rgba = image_array(base)
    tier = image_array(mask_image)[..., 0] > 0.5
    bones = cp.strongest_bone(body)
    names = sorted(set(bones))
    index = np.array([names.index(b) for b in bones], np.int32)
    pos, bone, rest_z = ct.rasterise(body, base.size, index)
    covered = (bone >= 0).astype(np.float32)
    pos, bone, rest_z = ct.dilate(pos, bone, rest_z)
    settings = dict(spec['texture']); settings['tier_mask'] = tier
    lin = ct.recolour(rgba[..., :3], bone, names, settings, pos, rest_z)
    mask = ct.blood_mask(pos, (bone >= 0) * 1.0, wounds)
    lin = ct.paint_blood(lin, mask, pos)
    save_array(os.path.join(pl.TEX, f'{name}_basecolor.png'), ct.linear_to_srgb(lin))
    for suffix in ('source', 'mask'):
        os.remove(paths[suffix])
    print('TEXTURE', name, base.size, 'covered', round(float(covered.mean()), 3), 'blood', round(float(mask.mean()), 4))


def build(name, spec):
    """spec additions over the outdoor script: 'capture' (callable(arm) -> info, run on the posed armature),
    'extra' (callable(level, mats, info) -> [objects] joined into each LOD: ropes, chains, hooks, poles),
    'materials' ({material name: texture}), 'tints' ({material name: linear rgb} multiplied into COLOR_0 after the
    occlusion), 'post' (callable(baked, arm, info) editing the baked body before texturing), 'occlusion'
    (vertex_occlusion keywords), 'drop' (extra vertex groups to drop)."""
    pl.reset()
    arm, body = cp.load(os.path.join(MODELS, spec['model']))
    cp.place(arm, spec['rotation'], spec['hips'])
    cp.pose(arm, spec['pose'])
    baked = cp.bake(arm, body, name, drop_groups=('Knife',) + tuple(spec.get('drop', ())),
                    keep_groups=spec.get('keep'))
    spec = dict(spec, stakes=spec.get('stakes', []) + impale(arm, spec.get('impale', [])))
    info = spec['capture'](arm) if 'capture' in spec else None
    if 'post' in spec:
        spec['post'](baked, arm, info)
    wounds = stake_wounds(baked, spec['stakes']) + bone_wounds(arm, spec.get('wounds', []))
    cuts = stump_cuts(arm, spec.get('stumps', []))
    bpy.data.objects.remove(body); bpy.data.objects.remove(arm)
    texture(name, spec, baked, wounds)
    mats = {'Body': ll.material('Body', name), 'Stake': ll.material('Stake', 'stake'),
            'Flesh': ll.material('Flesh', 'stake')}
    for key, tex in spec.get('materials', {}).items():
        mats[key] = ll.material(key, tex)
    baked.data.materials.clear(); baked.data.materials.append(mats['Body'])
    if cuts:
        seal_stumps(baked, spec, mats['Flesh'], cuts)
    for p in baked.data.polygons:
        p.use_smooth = True
    lods = []
    occlusion = dict(rays=None, distance=0.25, strength=0.6)
    occlusion.update(spec.get('occlusion', {}))
    for level, target in enumerate(spec.get('levels', LEVELS)):
        copy = baked.copy(); copy.data = baked.data.copy(); bpy.context.scene.collection.objects.link(copy)
        for g in list(copy.vertex_groups):
            copy.vertex_groups.remove(g)
        if 'rest' in copy.data.attributes:
            copy.data.attributes.remove(copy.data.attributes['rest'])
        pl.decimate_to(copy, target)
        cp.clean(copy)
        parts = [copy] + [stake(f'stake{level}_{i}', *s, STAKE_SIDES[level], mats['Stake'], i) for i, s in
                          enumerate(spec['stakes'])]
        if 'extra' in spec:
            parts += spec['extra'](level, mats, info)
        for part in parts[1:]:
            bpy.ops.object.select_all(action='DESELECT'); part.select_set(True)
            bpy.context.view_layer.objects.active = part
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        obj = pl.join(f'{name}{level}', parts)
        kw = dict(occlusion); kw['rays'] = kw['rays'] or (40, 24, 16, 12)[level]
        occl = pl.vertex_occlusion(obj, **kw)
        tint(obj, spec.get('tints', {}))
        title = name.capitalize()
        obj.name = title if level == 0 else f'{title}_LOD{level}'; obj.data.name = obj.name
        print('LEVEL', level, obj.name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3))
        lods.append(obj)
    lo, hi = pl.bounds(lods[:1])
    print('BOUNDS', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
    bpy.data.objects.remove(baked)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ll.WORK, f'{name}.blend'))
    pl.export(lods, os.path.join(ll.WORK, f'{name}_export.glb'))


def tint(obj, tints):
    """Multiply each vertex's occlusion colour by its material's linear tint (the first face's material wins)."""
    if not tints:
        return
    me = obj.data
    names = [m.name.split('.')[0] for m in me.materials]
    attr = me.color_attributes['Color']
    seen = {}
    for polygon in me.polygons:
        for index in polygon.vertices:
            seen.setdefault(index, names[polygon.material_index])
    for index, mname in seen.items():
        factor = tints.get(mname)
        if factor is None:
            continue
        c = attr.data[index].color
        attr.data[index].color = (c[0] * factor[0], c[1] * factor[1], c[2] * factor[2], c[3])
