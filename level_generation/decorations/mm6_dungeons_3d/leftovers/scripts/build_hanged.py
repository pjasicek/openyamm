"""Hanged and hooked corpses `corpse`, `corpse07`, `corpse08`, `corpse11`, `corpse14`, `corpse15`, `corpse18`: MM6
peasants (mm6_pman.glb / mm6_pfem.glb, read only) posed with corpse_pose.py into the sprite's pose, baked static and
welded (corpse_common.py, copied from the outdoor corpse pipeline), optionally cut into pieces with flesh caps
(severed torso, legs, arms), recoloured and bloodied, hung on a noose rope or on butcher's hooks and chains
(hang_props.py). A corpse is one or more pieces, each a separately posed import of the same peasant, so their texels
never overlap in the shared atlas. After baking the whole corpse is lifted so its lowest point is on the ground; the
rope or chain top lands at top_fraction of the sprite (the body's share of the sprite's height), so the model's
proportions match the sprite at the binding height (logical height x scale).
Writes textures/<corpse>_{basecolor,normal,mr}.png and work/<corpse>_export.glb.
Usage: blender --background --python build_hanged.py -- <corpse> [--preview]"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leftovers_lib as ll  # noqa: E402
import corpse_common as cc  # noqa: E402
import corpse_pose as cp  # noqa: E402
import corpse_texture as ct  # noqa: E402
import hang_props as hp  # noqa: E402

pl = ll.pl
M = 'mixamorig:'
LEG_BONES = tuple(f'mixamorig:{side}{part}' for side in ('Left', 'Right')
                  for part in ('UpLeg', 'Leg', 'Foot', 'ToeBase'))
LEVELS = (4400, 1800, 680, 200)
ROPE_SIDES = (8, 6, 4, 3)
SKIRT = tuple(f'Skirt_{k}_{j}' for k in range(12) for j in (1, 2, 3))


def bone_point(arm, name, t=0.5):
    pb = arm.pose.bones[name]
    return (arm.matrix_world @ pb.head).lerp(arm.matrix_world @ pb.tail, t)


def bone_dir(arm, name):
    pb = arm.pose.bones[name]
    return (arm.matrix_world @ pb.tail - arm.matrix_world @ pb.head).normalized()


# ---------------------------------------------------------------- pose fragments
def skirt_down(direction=(0, 0, -1), sag=0.3, tatter=0.0):
    """Turn the whole skirt cone rigidly (it stays round the legs) to hang along the direction, then let each panel's
    lower bones sag part of the way toward the ground; tatter adds a seeded per-panel swing so the hem hangs
    irregularly, like rags."""
    ops = [('aim_group', [f'Skirt_{k}_1' for k in range(12)], [f'Skirt_{k}_3' for k in range(12)], direction)]
    for k in range(12):
        ops.append(('aim', f'Skirt_{k}_2', (0, 0, -1), sag))
        ops.append(('aim', f'Skirt_{k}_3', (0, 0, -1), sag))
        if tatter:
            ops.append(('rot', f'Skirt_{k}_2', (math.cos(k * 2.4), math.sin(k * 2.4), 0), tatter * math.sin(k * 5.1)))
            ops.append(('rot', f'Skirt_{k}_3', (math.sin(k * 1.7), math.cos(k * 1.7), 0),
                        1.5 * tatter * math.cos(k * 3.7)))
    return ops


def arms_down(spread=0.12, fore=(0.04, -0.08), side=1.0):
    return [('aim', f'{M}LeftArm', (spread, 0.02, -1), 1.0),
            ('aim', f'{M}LeftForeArm', (fore[0], fore[1], -1), 1.0, f'{M}LeftHand'),
            ('aim', f'{M}LeftHand', (0.02, -0.05, -1), 1.0),
            ('aim', f'{M}RightArm', (-spread, 0.02, -1), 1.0),
            ('aim', f'{M}RightForeArm', (-fore[0], fore[1], -1), 1.0, f'{M}RightHand'),
            ('aim', f'{M}RightHand', (-0.02, -0.05, -1), 1.0)]


def legs_hanging(bend=0.0):
    """Legs hanging straight, feet pointing down (dead weight); bend lifts the right knee a little."""
    return [('aim', f'{M}LeftUpLeg', (0.04, 0.0, -1), 1.0),
            ('aim', f'{M}LeftLeg', (0.02, 0.03, -1), 1.0),
            ('aim', f'{M}LeftFoot', (0.05, -0.45, -1), 1.0),
            ('aim', f'{M}RightUpLeg', (-0.04, -bend, -1), 1.0),
            ('aim', f'{M}RightLeg', (-0.02, bend * 0.6, -1), 1.0),
            ('aim', f'{M}RightFoot', (-0.05, -0.45, -1), 1.0)]


def noose_capture(arm):
    return {'neck': bone_point(arm, f'{M}Neck', 0.45), 'neck_dir': bone_dir(arm, f'{M}Neck'),
            'head_top': arm.matrix_world @ arm.pose.bones[f'{M}Head'].tail,
            'head': bone_point(arm, f'{M}Head', 0.3)}


def noose(knot_turns=4, knot_radius=0.028, wire=0.016, knot_length=0.11, rope_x=0.0, loop_radius=0.062,
          behind=0.07):
    """Rope from the sprite top straight down behind the head to a hangman's knot (a coil) over the back of the
    neck, then a loop round the neck."""
    def extra(level, mats, info):
        sides = ROPE_SIDES[level]
        neck, axis = info['neck'], info['neck_dir']
        side = axis.cross(Vector((1, 0, 0))).normalized()
        if side.y < 0:
            side = -side                             # toward the back of the neck (+y)
        other = axis.cross(side).normalized()
        ring = [neck + (side * math.cos(a) + other * math.sin(a)) * loop_radius
                for a in [2 * math.pi * k / (sides * 2) for k in range(sides * 2 + 1)]]
        parts = [hp.rope('noose', ring, wire * 0.9, max(3, sides - 2), mats['Rope'])]
        back = neck + side * loop_radius
        top_z = info['top']
        knot_bottom = Vector((neck.x + rope_x * 0.5, neck.y + behind, max(back.z, info['head'].z)))
        knot_top = knot_bottom + Vector((0, 0, knot_length))
        parts.append(hp.rope('noose_back', [back, back.lerp(knot_bottom, 0.5) + Vector((0, 0.01, 0)), knot_bottom],
                             wire, sides, mats['Rope']))
        if level < 3:
            parts.append(hp.coil('knot', knot_bottom, knot_top, knot_radius, wire * 0.85, knot_turns,
                                 max(3, sides - 2), mats['Rope'], ring_sides=(10, 8, 6)[level]))
        else:
            parts.append(hp.rope('knot', [knot_bottom, knot_top], knot_radius + wire, 4, mats['Rope']))
        parts.append(hp.rope('rope', [knot_top, Vector((knot_top.x + rope_x * 0.5, knot_top.y, top_z))], wire,
                             sides, mats['Rope']))
        return parts
    return extra


def chain_hooks(entries, link=0.05, wire=0.0065, hook_drop=0.035, hook_bend=0.032, hook_wire=0.008,
                detail=((10, 4), (6, 3))):
    """Chains from the sprite top down to J hooks. entries: [(target, facing)], target an info key (a captured
    point) or a fixed (x, y, z) after the lift onto the ground; the bend's lowest point catches the target and the
    bend opens toward facing (the shank stands on the other side)."""
    def extra(level, mats, info):
        parts = []
        for k, (target, facing) in enumerate(entries):
            point = info[target] if isinstance(target, str) else Vector(target)
            f = Vector(facing).normalized()
            bend_bottom = point + Vector((0, 0, -hook_wire))
            hook_top = bend_bottom + Vector((0, 0, hook_drop + hook_bend)) - f * hook_bend
            if level == 3 and len(entries) > 2:
                hook_top = point                     # many hooks: the coarsest level keeps only the chains
            else:
                parts.append(hp.hook(f'hook{k}', hook_top, hook_drop, hook_bend, hook_wire, mats['Steel'],
                                     sides=(8, 6, 4, 3)[level], facing=f))
            parts.append(hp.chain(f'chain{k}', Vector((hook_top.x, hook_top.y, info['top'])), hook_top, link, wire,
                                  mats['Steel'], level=level, twist_deg=37 * k, detail=detail))
        return parts
    return extra


# ---------------------------------------------------------------- cutting pieces apart
def cut_piece(obj, arm, cuts):
    """cuts: [(bone, t, region bone names, flip)]: a plane through the posed bone's point t (head -> tail) with its
    normal along the bone (reversed with flip) pointing to the side that stays; only the faces of vertices whose
    strongest bone is in region are cut. The cut is capped (material index 1, Flesh) and loose scraps removed."""
    bones = cp.strongest_bone(obj)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.active
    bm.verts.ensure_lookup_table()
    side_of = {v: bones[v.index] for v in bm.verts}
    caps = []
    for name, t, region, flip in cuts:
        point = bone_point(arm, name, t)
        normal = bone_dir(arm, name) * (-1 if flip else 1)
        verts = [v for v in bm.verts if side_of.get(v, '') in region]
        bm.verts.index_update(); bm.edges.index_update(); bm.faces.index_update()
        faces = sorted({f for v in verts for f in v.link_faces}, key=lambda f: f.index)
        edges = sorted({e for f in faces for e in f.edges}, key=lambda e: e.index)
        result = bmesh.ops.bisect_plane(bm, geom=verts + edges + faces, plane_co=point, plane_no=normal,
                                        clear_inner=True)
        cut_edges = [e for e in result['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and e.is_valid]
        # cap: a fan from the cut's centroid over every cut edge, facing away from the kept side
        if cut_edges:
            centre = sum((v.co for e in cut_edges for v in e.verts), Vector()) / (2 * len(cut_edges))
            hub = bm.verts.new(centre)
            for e in cut_edges:
                a, b = e.verts
                if (a.co - centre).cross(b.co - centre).dot(normal) > 0:
                    a, b = b, a
                try:
                    caps.append(bm.faces.new((hub, a, b)))
                except ValueError:
                    pass
    seen, scraps = set(), []
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
        if len(island) < 60:
            scraps += island
    bmesh.ops.delete(bm, geom=scraps, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    for f in caps:
        if f.is_valid:
            f.material_index = 1
            for loop in f.loops:
                loop[uv].uv = (0.5, 0.96)
    count = sum(1 for f in caps if f.is_valid)
    bm.to_mesh(obj.data); bm.free()
    print('CUT', obj.name, 'cap faces', count, 'scrap faces', len(scraps))


# ---------------------------------------------------------------- texture (corpse_common.texture plus green cloth)
def texture(name, spec, body, wounds):
    images = cc.glb_images(os.path.join(ll.MODELS, spec['model']))
    paths = {}
    for key, suffix in (('basecolor', 'source'), ('normal', 'normal'), ('metal_rough', 'mr'),
                        ('region_mask', 'mask')):
        blob = next(v for k, v in images.items() if key in k)
        paths[suffix] = os.path.join(ll.TEXTURES, f'{name}_{suffix}.png')
        with open(paths[suffix], 'wb') as f:
            f.write(blob)
    base = bpy.data.images.load(paths['source']); mask_image = bpy.data.images.load(paths['mask'])
    rgba = cc.image_array(base)
    tier = cc.image_array(mask_image)[..., 0] > 0.5
    bones = cp.strongest_bone(body)
    names = sorted(set(bones))
    index = np.array([names.index(b) for b in bones], np.int32)
    pos, bone, rest_z = ct.rasterise(body, base.size, index)
    pos, bone, rest_z = ct.dilate(pos, bone, rest_z)
    settings = dict(spec['texture']); settings['tier_mask'] = tier
    src = rgba[..., :3]
    lin = ct.recolour(src, bone, names, settings, pos, rest_z)
    if settings.get('green') is not None:
        # green cloth outside the region mask (the pfem bodice, pman tunic trim) -> the configured colour
        r, g, b = src[..., 0], src[..., 1], src[..., 2]
        green = (g > r * 1.06) & (g > b * 1.08) & ~tier
        lum = ct.srgb_to_linear(src) @ np.array([0.2126, 0.7152, 0.0722])
        tone = np.asarray(settings['green']) * np.clip(lum / 0.08, 0.3, 2.2)[..., None]
        lin[green] = tone[green]
    if settings.get('trousers') is not None:
        # the pman's cream trousers (legs above the knee or `shorts` height, and the hips below the belt)
        names_arr = np.array(names + [''])[bone]
        legs = (np.char.find(names_arr, 'UpLeg') >= 0) | (np.char.endswith(names_arr, 'Leg'))
        hips = (names_arr == f'{M}Hips') & (rest_z < 0.93)
        knee = settings.get('shorts', 0.12)
        area = (legs | hips) & (rest_z > knee) & ~tier & (src.max(-1) > 0.35)
        lum = ct.srgb_to_linear(src) @ np.array([0.2126, 0.7152, 0.0722])
        shade = np.clip(ct.box_blur(lum, 3) / float(np.median(lum[area])), 0.3, 1.4)[..., None] ** 0.8
        dirt = 1 - 0.35 * ct.value_noise(pos, 8.0, 29)[..., None]
        lin[area] = (np.asarray(settings['trousers']) * shade * dirt)[area]
    lum_all = ct.srgb_to_linear(src) @ np.array([0.2126, 0.7152, 0.0722])
    if settings.get('tier_skin'):
        # the region-mask garment as bare skin: the skin colour with blurred shading (no weave showing through)
        smooth = ct.box_blur(lum_all, 6)
        shade = np.clip(smooth / float(np.median(smooth[tier])), 0.35, 1.3)[..., None] ** 0.8
        bruise = ct.value_noise(pos, 9.0, 11)[..., None]
        skin = np.asarray(settings.get('pale', (0.52, 0.52, 0.58))) * shade * (1 - 0.15 * np.clip((bruise - 0.55) * 4, 0, 1))
        lin[tier] = skin[tier]
    if settings.get('tier_below') is not None:
        # the region-mask cloth below the belt (tunic hem, skirt) in its own colour
        below = tier & (rest_z < settings.get('belt', 0.97)) & (bone >= 0)
        tone = np.asarray(settings['tier_below']) * np.clip(lum_all / 0.09, 0.3, 2.2)[..., None]
        lin[below] = tone[below]
    if settings.get('rags') is not None:
        # torn cloth patches left on the region-mask garment above the belt (the rest stays skin)
        patch = tier & (rest_z >= settings.get('belt', 0.97)) & (ct.value_noise(pos, 14.0, 31) > 0.58)
        tone = np.asarray(settings['rags']) * np.clip(lum_all / 0.09, 0.4, 1.6)[..., None]
        lin[patch] = tone[patch]
    if settings.get('hair_all') is not None:
        # every head texel that is not skin (the whole scalp, whatever its painted hair colour)
        names_arr = np.array(names + [''])[bone]
        mx = src.max(-1); mn = src.min(-1)
        sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        head = np.char.startswith(names_arr, f'{M}Head')
        skin = (sat > 0.18) & (sat < 0.7) & (mx > 0.55) & (src[..., 0] > src[..., 2])
        scalp = head & ~skin
        tone = np.asarray(settings['hair_all']) * np.clip(lum_all / 0.05, 0.4, 2.0)[..., None]
        lin[scalp] = tone[scalp]
    if settings.get('loincloth') is not None:
        names_arr = np.array(names + [''])[bone]
        colour, top = settings['loincloth']
        skirt = np.char.startswith(names_arr, 'Skirt')
        mx = src.max(-1); mn = src.min(-1)
        lum = ct.srgb_to_linear(src) @ np.array([0.2126, 0.7152, 0.0722])
        shade = np.clip(ct.box_blur(lum, 4) / float(np.median(lum[skirt])), 0.3, 1.3)[..., None] ** 0.8
        cloth = skirt & (rest_z > top)
        lin[skirt] = (np.asarray(settings.get('pale', (0.52, 0.52, 0.58))) * shade)[skirt]
        lin[cloth] = (np.asarray(colour) * shade)[cloth]
    if settings.get('ribs') is not None:
        # exposed ribs: bone-white bars across the listed bones' texels (rest height stripes) in a torn patch
        names_arr = np.array(names + [''])[bone]
        bones_r, pitch = settings['ribs']
        area = np.isin(names_arr, bones_r) & (ct.value_noise(pos, 10.0, 37) > 0.5)
        bars = (np.sin(2 * np.pi * rest_z / pitch) > 0.4)[..., None]
        rib = np.where(bars, np.array([0.42, 0.36, 0.27]), np.array([0.12, 0.005, 0.004]))
        lin[area] = rib[area]
    if settings.get('shorts'):
        # trousers cut off at the knee: pale cloth below the rest-pose knee height becomes skin
        mx = src.max(-1); mn = src.min(-1)
        sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        cloth = (sat < 0.32) & (mx > 0.5) & (rest_z < settings['shorts']) & (rest_z > 0.12) & (bone >= 0) & ~tier
        lum = ct.srgb_to_linear(src) @ np.array([0.2126, 0.7152, 0.0722])
        shade = np.clip(ct.box_blur(lum, 4) / float(np.median(lum[cloth])), 0.25, 1.35)[..., None] ** 0.8
        lin[cloth] = (np.asarray(settings.get('pale', (0.52, 0.52, 0.58))) * shade)[cloth]
    mask = ct.blood_mask(pos, (bone >= 0) * 1.0, wounds)
    lin = ct.paint_blood(lin, mask * settings.get('blood', 1.0), pos)
    cc.save_array(os.path.join(ll.TEXTURES, f'{name}_basecolor.png'), ct.linear_to_srgb(lin))
    for suffix in ('source', 'mask'):
        os.remove(paths[suffix])
    print('TEXTURE', name, base.size, 'blood', round(float(mask.mean()), 4))


# ---------------------------------------------------------------- build
def pose(arm, ops):
    """corpse_pose.pose plus ('converge', [bones], point, amount): aim each bone from its head toward the world
    point (a skirt drawn in round the legs)."""
    for op in ops:
        if op[0] == 'converge':
            for name in op[1]:
                head = arm.matrix_world @ arm.pose.bones[name].head
                cp.pose(arm, [('aim', name, tuple(Vector(op[2]) - head), op[3])])
        else:
            cp.pose(arm, [op])


def shifted(value, offset):
    if isinstance(value, Vector):
        return value + offset
    if isinstance(value, list):
        return [shifted(v, offset) for v in value]
    return value


def pose_pieces(spec):
    pieces, wounds, info = [], [], {}
    for k, piece in enumerate(spec['pieces']):
        arm, body = cp.load(os.path.join(ll.MODELS, spec['model']))
        cp.place(arm, piece.get('rotation', Matrix.Identity(3)), piece['hips'])
        pose(arm, piece['pose'])
        baked = cp.bake(arm, body, f'piece{k}', drop_groups=('Knife',) + tuple(piece.get('drop', ())),
                        keep_groups=piece.get('keep'))
        # one shared body material in slot 0, so joined pieces keep a single body primitive
        if 'BodySlot' not in bpy.data.materials:
            bpy.data.materials.new('BodySlot')
        if len(baked.data.materials) == 0:
            baked.data.materials.append(None)
        baked.data.materials[0] = bpy.data.materials['BodySlot']
        if piece.get('cuts'):
            # a second slot so the caps keep material index 1 (Flesh) through to_mesh and the join
            if 'FleshSlot' not in bpy.data.materials:
                bpy.data.materials.new('FleshSlot')
            while len(baked.data.materials) < 1:
                baked.data.materials.append(None)
            baked.data.materials.append(bpy.data.materials['FleshSlot'])
            cut_piece(baked, arm, piece['cuts'])
        if 'capture' in piece:
            info.update(piece['capture'](arm))
        wounds += cc.bone_wounds(arm, piece.get('wounds', []))
        bpy.data.objects.remove(body); bpy.data.objects.remove(arm)
        pieces.append(baked)
    body = pl.join('body', pieces) if len(pieces) > 1 else pieces[0]
    zs = [v.co.z for v in body.data.vertices]
    offset = Vector((0, 0, -min(zs)))
    body.data.transform(Matrix.Translation(offset))
    info = {k: shifted(v, offset) for k, v in info.items()}
    wounds = [(tuple(Vector(c) + offset), r, run) for c, r, run in wounds]
    top = max(zs) + offset.z
    info['body_top'] = top
    info['top'] = top / spec['top_fraction']
    print('BODY', 'height', round(top, 3), 'total', round(info['top'], 3), 'tris', pl.triangles(body))
    return body, info, wounds


def materials(name):
    mats = {'Body': ll.material('Body', name), 'Flesh': ll.material('Flesh', 'stake'),
            'Rope': ll.material('Rope', 'rope'), 'Steel': ll.material('Steel', 'steel')}
    return mats


def preview(name, spec):
    pl.reset()
    body, info, _ = pose_pieces(spec)
    mats = {k: bpy.data.materials.new(k) for k in ('Rope', 'Steel', 'Flesh')}
    props = spec['extra'](0, mats, info) if 'extra' in spec else []
    out = os.path.join(ll.REVIEW, name); os.makedirs(out, exist_ok=True)
    pl.setup_render((512, 512))
    print('PREVIEW', pl.render_views([body] + props, out, 'pose', views=((0, 6), (40, 20), (90, 6))))


def build(name, spec):
    pl.reset()
    body, info, wounds = pose_pieces(spec)
    texture(name, spec, body, wounds)
    mats = materials(name)
    # assign the slots in place: clearing them would reset the caps' material index
    while len(body.data.materials) < 2:
        body.data.materials.append(None)
    body.data.materials[0] = mats['Body']; body.data.materials[1] = mats['Flesh']
    for p in body.data.polygons:
        p.use_smooth = True
    lods = []
    for level, target in enumerate(spec.get('levels', LEVELS)):
        copy = body.copy(); copy.data = body.data.copy(); bpy.context.scene.collection.objects.link(copy)
        for g in list(copy.vertex_groups):
            copy.vertex_groups.remove(g)
        if 'rest' in copy.data.attributes:
            copy.data.attributes.remove(copy.data.attributes['rest'])
        pl.decimate_to(copy, target)
        cp.clean(copy)
        parts = [copy] + (spec['extra'](level, mats, info) if 'extra' in spec else [])
        obj = pl.join(f'{name}{level}', parts)
        occl = pl.vertex_occlusion(obj, rays=(40, 24, 16, 12)[level], distance=0.25, strength=0.6, floor=False)
        cc.tint(obj, spec.get('tints', {}))
        title = name.capitalize()
        obj.name = title if level == 0 else f'{title}_LOD{level}'; obj.data.name = obj.name
        print('LEVEL', level, obj.name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3))
        lods.append(obj)
    lo, hi = pl.bounds(lods[:1])
    print('BOUNDS', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
    bpy.data.objects.remove(body)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ll.WORK, f'{name}.blend'))
    pl.export(lods, os.path.join(ll.WORK, f'{name}_export.glb'))


# ---------------------------------------------------------------- the corpses
UPPER = tuple(f'{M}{b}' for b in ('Spine', 'Spine1', 'Spine2', 'Neck', 'Head', 'LeftShoulder', 'LeftArm',
                                   'LeftForeArm', 'LeftHand', 'RightShoulder', 'RightArm', 'RightForeArm',
                                   'RightHand')) + ('LeftForeArmTwist1', 'LeftForeArmTwist2', 'RightForeArmTwist1',
                                                    'RightForeArmTwist2', 'Braid_1', 'Braid_2', 'Braid_3')


class Keep:
    """keep_groups for cp.bake: the named bones plus, for kept hands, their finger bones."""
    def __init__(self, bones):
        self.bones = set(bones)
        self.hands = tuple(b for b in bones if b.endswith('Hand'))

    def __contains__(self, name):
        return name in self.bones or (name is not None and any(name.startswith(h) for h in self.hands))


def run(name):
    args = sys.argv[sys.argv.index('--') + 1:]
    (preview if '--preview' in args else build)(name, CORPSES[name])


CORPSES = {
    # Hanged man: long dark hair, bare grey-blue chest with white shirt rags, ragged khaki trousers; head lolling
    # forward and to the right, arms and legs hanging, feet pointing down. Body 0.795 of the sprite (rope above).
    'corpse': {
        'model': 'mm6_pman.glb', 'top_fraction': 0.795,
        'pieces': [{'hips': (0, 0, 0.95), 'capture': noose_capture,
                    'pose': [('aim', f'{M}Spine', (0.02, 0.02, 1), 1.0),
                             ('aim', f'{M}Spine2', (0.03, 0.04, 1), 1.0),
                             ('aim', f'{M}Neck', (0.25, -0.2, 1), 1.0),
                             ('aim', f'{M}Head', (0.45, -0.45, 0.75), 1.0)]
                            + arms_down(0.1) + legs_hanging(0.08),
                    'wounds': [(f'{M}Spine1', 0.5, 0.06, 0.25), (f'{M}LeftForeArm', 0.5, 0.04, 0.12, f'{M}LeftHand'),
                               (f'{M}RightLeg', 0.7, 0.05, 0.2), (f'{M}LeftLeg', 0.4, 0.04, 0.15),
                               (f'{M}Neck', 0.5, 0.05, 0.1)]}],
        'texture': {'hair_all': (0.006, 0.005, 0.007), 'tier_skin': True, 'trousers': (0.26, 0.19, 0.06),
                    'tier_below': (0.26, 0.19, 0.06), 'rags': (0.42, 0.42, 0.40),
                    'pale': (0.30, 0.34, 0.46), 'pale_leather': True, 'shorts': 0.40},
        'tints': {'Body': (0.334, 0.282, 0.28), 'Rope': (0.59, 0.49, 0.45)},
        'extra': noose(),
    },
    # Hanged woman: blonde hair over the face, pale pink-white ragged dress with an orange belt, bloodied; head
    # fallen to her left (screen right), arms hanging. Body 0.814 of the sprite.
    'corpse07': {
        'model': 'mm6_pfem.glb', 'top_fraction': 0.814,
        'pieces': [{'hips': (0, 0, 0.95), 'capture': noose_capture,
                    'pose': [('aim', f'{M}Spine', (-0.03, 0.02, 1), 1.0),
                             ('aim', f'{M}Spine2', (-0.02, 0.04, 1), 1.0),
                             ('aim', f'{M}Neck', (0.3, -0.15, 1), 1.0),
                             ('aim', f'{M}Head', (0.6, -0.35, 0.7), 1.0),
                             ('aim', 'Braid_1', (0, 0, -1), 1.0), ('aim', 'Braid_2', (0, 0, -1), 1.0),
                             ('aim', 'Braid_3', (0, 0, -1), 1.0)]
                            + arms_down(0.14) + legs_hanging(0.05)
                            + [('aim', f'Skirt_{k}_1', (0, 0, -1), 0.55) for k in range(12)]
                            + skirt_down((0, 0, -1), sag=1.0, tatter=7),
                    'drop': tuple(f'Skirt_{k}_3' for k in range(12)),
                    'wounds': [(f'{M}Spine1', 0.4, 0.07, 0.3), (f'{M}Hips', 0.2, 0.06, 0.35),
                               ('Skirt_2_2', 0.8, 0.06, 0.25), ('Skirt_7_2', 0.6, 0.06, 0.3),
                               ('Skirt_10_2', 0.9, 0.05, 0.2), ('Skirt_4_2', 0.5, 0.05, 0.25),
                               (f'{M}LeftLeg', 0.6, 0.05, 0.2), (f'{M}RightLeg', 0.8, 0.05, 0.15),
                               (f'{M}LeftForeArm', 0.6, 0.04, 0.12, f'{M}LeftHand')]}],
        'texture': {'hair_all': (0.42, 0.30, 0.10), 'tier': (0.30, 0.12, 0.10), 'cloth': (0.50, 0.36, 0.33),
                    'cloth_dirt': 0.6, 'pale': (0.36, 0.37, 0.45), 'green': (0.32, 0.09, 0.07), 'feet': (0.30, 0.28, 0.32),
                    'leather': (0.40, 0.14, 0.03)},
        'tints': {'Body': (0.524, 0.506, 0.511), 'Rope': (0.587, 0.522, 0.547)},
        'extra': noose(),
    },
    # Hanged man's upper body, cut through at the waist: bare and white, soaked in blood, neck broken with the head
    # laid on the right shoulder, arms hanging straight below the cut. Big hangman's knot. Body 0.739 of the sprite.
    'corpse08': {
        'model': 'mm6_pman.glb', 'top_fraction': 0.739,
        'pieces': [{'hips': (0, 0, 0.95), 'capture': noose_capture, 'keep': Keep(UPPER + (f'{M}Hips',)),
                    'cuts': [(f'{M}Hips', 0.0, {f'{M}Hips', f'{M}Spine'}, False)],
                    'pose': [('aim', f'{M}Spine', (-0.12, 0.0, 1), 1.0),
                             ('aim', f'{M}Spine2', (-0.15, 0.03, 1), 1.0),
                             ('aim', f'{M}Neck', (0.75, -0.1, 0.65), 1.0),
                             ('aim', f'{M}Head', (1, -0.25, 0.1), 1.0)]
                            + arms_down(0.16, (0.0, -0.05)),
                    'wounds': [(f'{M}Hips', 0.0, 0.16, 0.3), (f'{M}Spine1', 0.5, 0.12, 0.4),
                               (f'{M}Spine2', 0.7, 0.115, 0.45), (f'{M}LeftShoulder', 0.5, 0.08, 0.4),
                               (f'{M}Spine1', 0.0, 0.12, 0.3),
                               (f'{M}Spine2', 0.6, 0.09, 0.35), (f'{M}Spine', 0.5, 0.10, 0.3), (f'{M}LeftArm', 0.3, 0.05, 0.25),
                               (f'{M}RightArm', 0.4, 0.05, 0.2), (f'{M}Neck', 0.5, 0.06, 0.2),
                               (f'{M}RightForeArm', 0.8, 0.04, 0.12, f'{M}RightHand')]}],
        'texture': {'hair_all': (0.36, 0.26, 0.09), 'tier_skin': True, 'pale_cloth': True,
                    'pale_leather': True, 'pale': (0.55, 0.55, 0.62)},
        'tints': {'Body': (0.318, 0.273, 0.273), 'Rope': (0.43, 0.38, 0.40), 'Flesh': (0.5, 0.4, 0.4)},
        'extra': noose(knot_turns=6, knot_radius=0.045, wire=0.024, knot_length=0.2, behind=0.04),
    },
    # Hanged man in a ragged grey coat and trousers with a red cap (the scalp recoloured), dark grey-green skin, head
    # bowed onto the chest, arms hanging, bare feet. Body 0.798 of the sprite.
    'corpse15': {
        'model': 'mm6_pman.glb', 'top_fraction': 0.798,
        'pieces': [{'hips': (0, 0, 0.95), 'capture': noose_capture,
                    'pose': [('aim', f'{M}Spine', (0.0, 0.03, 1), 1.0),
                             ('aim', f'{M}Spine2', (0.02, 0.06, 1), 1.0),
                             ('aim', f'{M}Neck', (0.08, -0.55, 1), 1.0),
                             ('aim', f'{M}Head', (0.15, -0.95, 0.35), 1.0)]
                            + arms_down(0.08, (0.02, -0.12)) + legs_hanging(0.04),
                    'wounds': [(f'{M}Spine1', 0.5, 0.05, 0.25), (f'{M}Spine2', 0.3, 0.04, 0.2),
                               (f'{M}LeftLeg', 0.5, 0.04, 0.15), (f'{M}RightUpLeg', 0.7, 0.04, 0.15),
                               (f'{M}Neck', 0.5, 0.05, 0.12)]}],
        'texture': {'hair_all': (0.40, 0.012, 0.01), 'tier': (0.20, 0.20, 0.18), 'trousers': (0.17, 0.17, 0.15),
                    'tier_below': (0.20, 0.20, 0.18), 'pale': (0.17, 0.19, 0.17), 'leather': (0.10, 0.09, 0.08),
                    'feet': (0.26, 0.24, 0.20), 'blood': 0.8},
        'tints': {'Body': (0.393, 0.313, 0.341), 'Rope': (0.278, 0.252, 0.241)},
        'extra': noose(),
    },
    # Woman hung by her crossed wrists from a butcher's hook on a chain: arms straight up, blonde hair, tan skin
    # with cuts, the skirt gone (brown bodice and loincloth left), legs hanging. Body 0.80 of the sprite.
    'corpse11': {
        'model': 'mm6_pfem.glb', 'top_fraction': 0.80, 'levels': (4300, 1800, 680, 200),
        'pieces': [{'hips': (0, 0, 0.95), 'drop': tuple(f'Skirt_{k}_3' for k in range(12)),
                    'capture': lambda arm: {'wrists': (bone_point(arm, f'{M}LeftHand', 0.0) +
                                                       bone_point(arm, f'{M}RightHand', 0.0)) / 2
                                            + Vector((0, 0, 0.01))},
                    'pose': [('aim', f'{M}Spine', (0.0, 0.0, 1), 1.0),
                             ('aim', f'{M}Spine2', (0.03, 0.03, 1), 1.0),
                             ('aim', f'{M}LeftArm', (-0.2, 0.06, 1), 1.0),
                             ('aim', f'{M}LeftForeArm', (-0.62, 0.0, 1), 1.0, f'{M}LeftHand'),
                             ('aim', f'{M}LeftHand', (-0.3, 0.0, 1), 1.0),
                             ('aim', f'{M}RightArm', (0.2, 0.06, 1), 1.0),
                             ('aim', f'{M}RightForeArm', (0.62, 0.0, 1), 1.0, f'{M}RightHand'),
                             ('aim', f'{M}RightHand', (0.3, 0.0, 1), 1.0),
                             ('aim', f'{M}Neck', (-0.15, -0.2, 1), 1.0),
                             ('aim', f'{M}Head', (-0.35, -0.45, 0.85), 1.0),
                             ('aim', 'Braid_1', (0, 0, -1), 1.0), ('aim', 'Braid_2', (0, 0, -1), 1.0),
                             ('aim', 'Braid_3', (0, 0, -1), 1.0)]
                            + legs_hanging(0.0)
                            + [('converge', [f'Skirt_{k}_1' for k in range(12)], (0.0, 0.0, 0.25), 1.0),
                               ('converge', [f'Skirt_{k}_2' for k in range(12)], (0.0, 0.0, -0.3), 1.0)],
                    'wounds': [(f'{M}LeftHand', 0.0, 0.05, 0.3), (f'{M}RightHand', 0.0, 0.05, 0.3),
                               (f'{M}LeftArm', 0.6, 0.025, 0.12), (f'{M}Spine1', 0.4, 0.03, 0.15),
                               (f'{M}Spine', 0.6, 0.025, 0.12), (f'{M}LeftUpLeg', 0.5, 0.025, 0.15),
                               (f'{M}RightUpLeg', 0.3, 0.025, 0.12), (f'{M}RightLeg', 0.4, 0.02, 0.1)]}],
        'texture': {'hair_all': (0.50, 0.36, 0.11), 'tier': (0.46, 0.25, 0.17), 'pale_cloth': True,
                    'loincloth': ((0.12, 0.06, 0.03), 0.80),
                    'pale': (0.46, 0.25, 0.17), 'green': (0.12, 0.06, 0.03), 'leather': (0.12, 0.06, 0.03),
                    'blood': 0.8},
        'tints': {'Body': (0.405, 0.336, 0.367), 'Steel': (0.348, 0.524, 0.728)},
        'extra': chain_hooks([('wrists', (1, 0, 0))], link=0.065, wire=0.007, hook_drop=0.06, hook_bend=0.04,
                             hook_wire=0.009),
    },
    # Headless, armless torso (neck, shoulders and waist cut through and soaked) on a hook through the neck stump,
    # hanging from a chain. White skin, the tunic turned to skin. Torso 0.48 of the sprite.
    'corpse18': {
        'model': 'mm6_pman.glb', 'top_fraction': 0.48,
        'pieces': [{'hips': (0, 0, 0.95),
                    'keep': Keep(tuple(f'{M}{b}' for b in ('Hips', 'Spine', 'Spine1', 'Spine2', 'Neck',
                                                           'LeftShoulder', 'RightShoulder', 'LeftArm',
                                                           'RightArm'))),
                    'cuts': [(f'{M}Hips', 0.2, {f'{M}Hips', f'{M}Spine'}, False),
                             (f'{M}Neck', 0.15, {f'{M}Neck', f'{M}Spine2'}, True),
                             (f'{M}LeftArm', 0.12, {f'{M}LeftArm', f'{M}LeftShoulder'}, True),
                             (f'{M}RightArm', 0.12, {f'{M}RightArm', f'{M}RightShoulder'}, True)],
                    'capture': lambda arm: {'stump': bone_point(arm, f'{M}Spine2', 0.75)},
                    'pose': [('aim', f'{M}Spine', (0.06, 0.0, 1), 1.0),
                             ('aim', f'{M}LeftArm', (1, 0, -0.35), 1.0), ('aim', f'{M}RightArm', (-1, 0, -0.35), 1.0)],
                    'wounds': [(f'{M}Neck', 0.1, 0.10, 0.25), (f'{M}LeftArm', 0.1, 0.09, 0.3),
                               (f'{M}RightArm', 0.1, 0.09, 0.3), (f'{M}Hips', 0.2, 0.14, 0.2),
                               (f'{M}Spine2', 0.4, 0.04, 0.2), (f'{M}Spine1', 0.6, 0.035, 0.15)]}],
        'texture': {'hair_all': (0.3, 0.3, 0.3), 'tier_skin': True, 'pale_cloth': True,
                    'pale_leather': True, 'trousers': (0.58, 0.57, 0.60), 'pale': (0.58, 0.57, 0.60)},
        'tints': {'Body': (0.435, 0.406, 0.438), 'Steel': (0.188, 0.301, 0.459), 'Flesh': (0.5, 0.4, 0.4)},
        'extra': chain_hooks([('stump', (1, 0, 0))], link=0.062, wire=0.0095, hook_drop=0.13, hook_bend=0.045,
                             hook_wire=0.013, detail=((8, 4), (4, 3))),
    },
    # Butcher's rack: six chains with hooks; a lower body (khaki shorts, seen from behind) on two of them, through
    # the waist and the raised left knee; a severed right arm on one; an upper torso with exposed ribs lying on its
    # side on another, its left arm hanging; two hooks empty. Positions traced from the sprite (x2 px / 272 per m).
    'corpse14': {
        'model': 'mm6_pman.glb', 'top_fraction': 0.783, 'levels': (2400, 1150, 460, 160),
        'pieces': [
            {'rotation': Matrix.Rotation(math.pi, 3, 'Z'), 'hips': (-0.10, 0.0, 0.875),
             'keep': Keep(tuple(f'{M}{b}' for b in ('Hips', 'Spine')) + LEG_BONES),
             'cuts': [(f'{M}Hips', 0.85, {f'{M}Hips', f'{M}Spine'}, True)],
             'capture': lambda arm: {'knee': bone_point(arm, f'{M}LeftUpLeg', 0.8) + Vector((0, 0, 0.03)),
                                     'waist': bone_point(arm, f'{M}Hips', 0.6)},
             'pose': [('aim', f'{M}RightUpLeg', (0.02, 0.0, -1), 1.0),
                      ('aim', f'{M}RightLeg', (0.0, 0.03, -1), 1.0),
                      ('aim', f'{M}RightFoot', (0.0, 0.4, -1), 1.0),
                      ('aim', f'{M}LeftUpLeg', (-0.57, 0.05, 0.82), 1.0),
                      ('aim', f'{M}LeftLeg', (-0.26, 0.0, -0.97), 1.0),
                      ('aim', f'{M}LeftFoot', (-0.1, 0.3, -1), 1.0)],
             'wounds': [(f'{M}Hips', 0.85, 0.14, 0.3), (f'{M}LeftUpLeg', 0.8, 0.05, 0.2),
                        (f'{M}RightUpLeg', 0.6, 0.03, 0.15), (f'{M}RightLeg', 0.5, 0.03, 0.12)]},
            {'hips': (0.0, 0.0, 0.884),
             'keep': Keep((f'{M}RightArm', f'{M}RightForeArm', 'RightForeArmTwist1', 'RightForeArmTwist2',
                           f'{M}RightHand', f'{M}RightShoulder')),
             'cuts': [(f'{M}RightArm', 0.08, {f'{M}RightArm', f'{M}RightShoulder'}, False)],
             'capture': lambda arm: {'arm': bone_point(arm, f'{M}RightArm', 0.22) + Vector((0.035, 0, 0))},
             'pose': [('move', f'{M}RightArm', (0.02, 0.02, 1.46)),
                      ('aim', f'{M}RightArm', (0.27, 0.0, -0.96), 1.0),
                      ('aim', f'{M}RightForeArm', (-0.15, -0.05, -0.99), 1.0, f'{M}RightHand'),
                      ('aim', f'{M}RightHand', (-0.1, -0.1, -1), 1.0)],
             'wounds': [(f'{M}RightArm', 0.05, 0.06, 0.25), (f'{M}RightArm', 0.6, 0.03, 0.15)]},
            {'rotation': Matrix.Rotation(math.radians(80), 3, 'Y'), 'hips': (0.04, 0.05, 0.78),
             'keep': Keep(tuple(f'{M}{b}' for b in ('Spine', 'Spine1', 'Spine2', 'Neck', 'LeftShoulder', 'LeftArm',
                                                    'LeftForeArm', 'LeftHand', 'RightShoulder', 'RightArm'))
                          + ('LeftForeArmTwist1', 'LeftForeArmTwist2')),
             'cuts': [(f'{M}Spine1', 0.15, {f'{M}Spine', f'{M}Spine1'}, False),
                      (f'{M}Neck', 0.2, {f'{M}Neck', f'{M}Spine2'}, True),
                      (f'{M}RightArm', 0.1, {f'{M}RightArm', f'{M}RightShoulder'}, True)],
             'capture': lambda arm: {'ribs': bone_point(arm, f'{M}Spine2', 0.3) + Vector((0, 0, 0.06))},
             'pose': [('aim', f'{M}LeftArm', (0.05, 0.0, -1), 1.0),
                      ('aim', f'{M}LeftForeArm', (-0.1, -0.1, -1), 1.0, f'{M}LeftHand'),
                      ('aim', f'{M}LeftHand', (-0.2, -0.1, -1), 1.0)],
             'wounds': [(f'{M}Spine1', 0.15, 0.12, 0.25), (f'{M}Neck', 0.2, 0.07, 0.2),
                        (f'{M}RightArm', 0.1, 0.07, 0.2), (f'{M}Spine2', 0.5, 0.06, 0.2)]},
        ],
        'texture': {'hair_all': (0.3, 0.3, 0.3), 'tier_skin': True, 'tier_below': (0.20, 0.15, 0.07),
                    'belt': 0.97, 'trousers': (0.20, 0.15, 0.07), 'shorts': 0.58, 'pale_leather': True,
                    'pale': (0.50, 0.50, 0.54), 'ribs': ([f'{M}Spine1', f'{M}Spine2'], 0.032)},
        'tints': {'Body': (0.352, 0.301, 0.325), 'Steel': (0.43, 0.624, 0.853), 'Flesh': (0.5, 0.4, 0.4)},
        'extra': chain_hooks([('knee', (1, 0, 0)), ('waist', (1, 0, 0)), ((-0.085, 0.0, 1.08), (-1, 0, 0)),
                              ('arm', (-1, 0, 0)), ('ribs', (-1, 0, 0)), ((0.38, 0.0, 1.20), (1, 0, 0))],
                             link=0.07, wire=0.007, hook_drop=0.05, hook_bend=0.035, hook_wire=0.008,
                             detail=((4, 3),)),
    },
}


if __name__ == '__main__':
    run(sys.argv[sys.argv.index('--') + 1])
