"""Leftover MM6 dungeon corpses, batch B: the severed heads `corpse01` (old man's head in a wicker basket), `corpse09`
(bearded head on a stake) and `corpse10` (long-haired woman's head on a spike through the skull, one eye out), and the
bodies `corpse02` (hung by wrists and ankles under a rack) and `corpse03` (three bodies on one pole).
Bodies and heads are the project's rigged MM6 peasants (assets_dev/worlds/mm6/models/mm6_pman/pfem/pmn2.glb, read
only) posed with corpse_pose.py world-space bone operations plus a two-bone reach (IK) toward a world point, baked
static and welded. Heads keep the neck and everything below the head bone, cut square across the neck with a flesh
cap; their texture is cropped to the 1K head half of the peasant atlas. Textures are recoloured to the sprite's
measured colours (linear sRGB of the sprite's mean region colours) and bloodied at the wounds (corpse_texture.py).
Props: stakes (corpse_common.stake), a lathe-built wicker basket, a hair curtain (alpha-tested strands) and an
eyeball, a rack of wooden poles with rope bindings, a pole for the three bodies.
Writes textures/<corpse>_*.png and work/<corpse>_export.glb.
Usage: blender --background --python build_corpses_b.py -- <corpse> [--preview]"""
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
IDENTITY = Matrix.Identity(3)


def lin(rgb):
    return tuple(float(ct.srgb_to_linear(np.array(c / 255.0))) for c in rgb)


def roll(degrees):
    return Matrix.Rotation(math.radians(degrees), 3, 'X')


def rot(axis, degrees):
    return Matrix.Rotation(math.radians(degrees), 3, axis)


# ---------------------------------------------------------------- posing helpers
def world_head(arm, bone):
    return arm.matrix_world @ arm.pose.bones[bone].head


def world_tail(arm, bone):
    return arm.matrix_world @ arm.pose.bones[bone].tail


def reach(arm, upper, lower, end, target, pole):
    """Two-bone reach: turn `upper` and `lower` so the head of `end` lands on the world target (clamped to the
    limb's length), the middle joint bending toward the world pole direction."""
    s = world_head(arm, upper); e = world_head(arm, lower); w = world_head(arm, end)
    l1, l2 = (e - s).length, (w - e).length
    target = Vector(target); d = target - s
    dist = min(d.length, (l1 + l2) * 0.999); dn = d.normalized()
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist); h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    p = Vector(pole); p = (p - dn * p.dot(dn)).normalized()
    elbow = s + dn * a + p * h
    cp.pose(arm, [('aim', upper, tuple(elbow - s), 1.0)])
    cp.pose(arm, [('aim', lower, tuple(s + dn * dist - world_head(arm, lower)), 1.0, end)])


def run_pose(arm, ops):
    """corpse_pose ops plus ('reach', upper, lower, end, target, pole)."""
    for op in ops:
        if op[0] == 'reach':
            reach(arm, *op[1:])
        else:
            cp.pose(arm, [op])


def descendants(arm, bone):
    out = [bone]
    for child in arm.data.bones[bone].children_recursive:
        out.append(child.name)
    return out


def load(spec, rotation, hips):
    arm, body = cp.load(os.path.join(ll.MODELS, spec['model']))
    cp.place(arm, rotation, hips)
    run_pose(arm, spec['pose'])
    return arm, body


def save_png(path, srgb, alpha=None, top_down=True):
    """Write an sRGB float array (rows top-down unless top_down=False) through Blender (no PIL in its Python)."""
    h, w = srgb.shape[:2]
    a = np.ones((h, w)) if alpha is None else alpha
    px = np.dstack([np.clip(srgb, 0, 1), np.clip(a, 0, 1)]).astype(np.float32)
    if top_down:
        px = px[::-1]
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=alpha is not None)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path; img.file_format = 'PNG'; img.save()
    bpy.data.images.remove(img)


def crop_png(path, x0, width):
    """Crop columns x0..x0+width of a non-colour PNG in place (Blender pixel rows are bottom-up; rows unchanged)."""
    img = bpy.data.images.load(path); img.colorspace_settings.name = 'Non-Color'
    a = cc.image_array(img)[:, x0:x0 + width, :3]
    bpy.data.images.remove(img)
    out = bpy.data.images.new(os.path.basename(path), width, a.shape[0], alpha=False)
    out.colorspace_settings.name = 'Non-Color'
    out.pixels.foreach_set(np.dstack([a, np.ones(a.shape[:2])]).astype(np.float32).ravel())
    out.filepath_raw = path; out.file_format = 'PNG'; out.save()
    bpy.data.images.remove(out)


# ---------------------------------------------------------------- heads
def neck_cut(obj, arm, t, flesh_index):
    """Cut the head off square across the neck bone at t (0 base .. 1 top); cap the cut (flesh material); drop
    scraps. Returns the cap centre (world)."""
    head, tail = world_head(arm, M + 'Neck'), world_tail(arm, M + 'Neck')
    point = head.lerp(tail, t); normal = (tail - head).normalized()
    bones = cp.strongest_bone(obj)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.active
    bm.verts.ensure_lookup_table()
    # everything below the plane goes (hair hanging lower at the back is cut level with the stump)
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    result = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=point, plane_no=normal, clear_inner=True)
    cut = [e for e in result['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    existing = set(bm.faces)
    bmesh.ops.holes_fill(bm, edges=cut, sides=0)
    new = [f for f in bm.faces if f not in existing]
    bmesh.ops.triangulate(bm, faces=new)
    caps = [f for f in bm.faces if f not in existing]
    seen, scraps = set(), []
    for f in bm.faces:
        if f in seen:
            continue
        island, stack = [], [f]; seen.add(f)
        while stack:
            g = stack.pop(); island.append(g)
            for e in g.edges:
                for k in e.link_faces:
                    if k not in seen:
                        seen.add(k); stack.append(k)
        if len(island) < 40:
            scraps += island
    bmesh.ops.delete(bm, geom=scraps, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    for f in caps:
        if f.is_valid:
            f.material_index = flesh_index
            for loop in f.loops:
                loop[uv].uv = (0.5, 0.96)
    bm.to_mesh(obj.data); bm.free()
    print('NECK cut', len(cut), 'cap faces', len(caps), 'scraps', len(scraps))
    return point, normal


def paint_blood(lin_c, mask, pos):
    """corpse_texture.paint_blood with the darker, browner blood of the dungeon sprites."""
    tone = np.array([0.22, 0.012, 0.006])
    dark = np.array([0.05, 0.004, 0.003])
    vary = (ct.value_noise(pos, 60.0, 23) ** 2)[..., None]
    blood = tone * (1 - vary) + dark * vary
    m = np.clip(mask, 0, 1)[..., None]
    return lin_c * (1 - m) + blood * m


def head_recolour(base_srgb, covered, spec, pos):
    """Head texels: skin (warm, saturated, bright) -> spec skin with its own shading; dark hair/beard -> spec hair
    keeping the hair's shading; pale low-saturation detail (eyes, teeth) kept."""
    lin_c = ct.srgb_to_linear(base_srgb)
    mx = base_srgb.max(-1); mn = base_srgb.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = base_srgb[..., 0], base_srgb[..., 1], base_srgb[..., 2]
    delta = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - b) / delta) % 6, np.where(mx == g, (b - r) / delta + 2, (r - g) / delta + 4)) * 60
    lum = lin_c @ np.array([0.2126, 0.7152, 0.0722])
    skin = (hue > 2) & (hue < 45) & (sat > 0.2) & (sat < spec.get('skin_sat', 0.62)) & (mx > spec.get('skin_min', 0.6))
    detail = (sat < 0.22) & (mx > 0.55)
    hair = ~skin & ~detail
    out = lin_c.copy()
    for mask, colour, gamma in ((skin, spec['skin'], 0.9), (hair, spec['hair'], 1.0)):
        sel = mask & (covered > 0)
        if not sel.any():
            continue
        shade = np.clip(lum / float(np.median(lum[sel])), 0.2, spec.get('highlight', 1.7))[..., None] ** gamma
        out[mask] = (np.asarray(colour) * shade)[mask]
    if spec.get('bruise'):
        bruise = ct.value_noise(pos, 9.0, 11)
        out[skin] *= (1 - spec['bruise'] * np.clip((bruise - 0.5) * 3, 0, 1))[skin][..., None]
    return out


def head_texture(name, spec, obj, wounds):
    """Recoloured, bloodied head-half of the peasant atlas (+ normal / mr crops); remaps the object's u."""
    images = cc.glb_images(os.path.join(ll.MODELS, spec['model']))
    paths = {}
    for key, suffix in (('basecolor', 'source'), ('normal', 'normal'), ('metal_rough', 'mr')):
        blob = next(v for k, v in images.items() if key in k)
        paths[suffix] = os.path.join(ll.TEXTURES, f'{name}_{suffix}.png')
        with open(paths[suffix], 'wb') as f:
            f.write(blob)
    base = bpy.data.images.load(paths['source'])
    W, H = base.size
    me = obj.data
    uvs = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get('uv', uvs)
    uvs = uvs.reshape(-1, 2)
    body_loops = uvs[:, 0] * W
    x0 = 1056                              # the 1K head atlas: x 1056..2080 (body atlas 0..1024, gutter)
    stray = (body_loops < x0 - 2) & ~((np.abs(uvs[:, 0] - 0.5) < 1e-4) & (np.abs(uvs[:, 1] - 0.96) < 1e-4))
    print('HEAD UV', 'loops', len(uvs), 'outside head atlas', int(stray.sum()))
    rgba = cc.image_array(base)
    names = sorted(set(cp.strongest_bone(obj)))
    index = np.array([names.index(b) for b in cp.strongest_bone(obj)], np.int32)
    pos, bone, rest_z = ct.rasterise(obj, base.size, index)
    covered = (bone >= 0).astype(np.float32)
    pos, bone, rest_z = ct.dilate(pos, bone, rest_z)
    out = head_recolour(rgba[..., :3], covered, spec['texture'], pos)
    mask = ct.blood_mask(pos, (bone >= 0) * 1.0, wounds)
    out = paint_blood(out, mask, pos) * texture_gain(spec)
    out = out[:, x0:x0 + 1024]
    cc.save_array(os.path.join(ll.TEXTURES, f'{name}_basecolor.png'), ct.linear_to_srgb(out))
    for suffix in ('normal', 'mr'):
        crop_png(paths[suffix], x0, 1024)
    os.remove(paths['source'])
    # remap u into the crop (flesh caps keep their stake-texture coordinates on another material)
    flesh = [i for i, m in enumerate(me.materials) if m.name.startswith('Flesh')]
    for poly in me.polygons:
        if poly.material_index in flesh:
            continue
        for li in poly.loop_indices:
            u = me.uv_layers.active.data[li].uv
            me.uv_layers.active.data[li].uv = (min(max((u.x * W - x0) / 1024, 0.0), 1.0), u.y)
    print('TEXTURE', name, 'blood', round(float(mask.mean()), 4))


def hair_texture(name, colour, seed=7):
    """Long hair strands: u across (strands), v along (0 at the root); ragged strand ends in the alpha below
    v = 0.75; streaky shading, the given sRGB mean colour."""
    rng = np.random.default_rng(seed)
    S = 512
    strands = 96
    col = np.arange(S) * strands // S
    shade = rng.uniform(0.55, 1.35, strands)[col]
    ends = rng.uniform(0.78, 1.0, strands)[col]
    v = (np.arange(S) + 0.5) / S
    fine = np.sin(np.arange(S)[None, :] * 0.9 + rng.uniform(0, 6, S)[None, :]) * 0.15 + 0.85
    value = shade[None, :] * fine * (0.8 + 0.2 * np.sin(v[:, None] * 40 + col[None, :]))
    alpha = (v[:, None] < ends[None, :]).astype(float)
    base = np.array(lin(colour))
    rgb = np.clip(base * value[..., None], 0, 1)
    # array rows run with v (row 0 = v 0): Blender's bottom-up pixel order
    save_png(os.path.join(ll.TEXTURES, f'{name}_basecolor.png'), ct.linear_to_srgb(rgb), alpha, top_down=False)
    mr = np.zeros((S, S, 3)); mr[..., 1] = 0.6
    save_png(os.path.join(ll.TEXTURES, f'{name}_mr.png'), mr)


def hair_curtain(name, centre, radius, top, hairline, bottom, flare, opening_deg, mat, level, seed=3):
    """Long loose hair as one double-sided sheet: a closed dome from `top` over the skull down to the hairline,
    then a curtain round the back and sides, open at the front by opening_deg, hanging to `bottom` and widening
    by `flare` there. u across the strands, v from 1 at the crown to 0 at the ends (the strand ends are cut out
    in the texture's alpha)."""
    rng = np.random.default_rng(seed)
    cols, rows = ((28, 14), (18, 9), (12, 6), (8, 4))[level]
    dome = 0.075
    open_half = math.radians(180 - opening_deg / 2)
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    wobble = rng.uniform(-1, 1, cols + 1)
    zs = [top - (top - bottom) * (j / rows) ** 1.25 for j in range(rows + 1)]
    grid = []
    for j, z in enumerate(zs):
        depth = top - z
        r = radius * math.sqrt(max(0.0, min(1.0, depth / dome)) * (2 - min(1.0, depth / dome)))
        r = max(r, radius * 0.12) + flare * max(0.0, (hairline - z) / max(hairline - bottom, 1e-6)) ** 1.5
        blend = min(1.0, max(0.0, (hairline - z) / 0.04))
        half = math.pi * (1 - blend) + open_half * blend
        row = []
        for i in range(cols + 1):
            ang = -half + 2 * half * i / cols           # 0 = back (+y)
            rr = r * (1 + 0.05 * wobble[i] * blend)
            row.append(bm.verts.new((centre[0] + rr * math.sin(ang), centre[1] + rr * math.cos(ang), z)))
        grid.append(row)
    for j in range(rows):
        for i in range(cols):
            f = bm.faces.new((grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1]))
            for loop, (u, v) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
                loop[uv].uv = (u / cols * 3.0, 1.0 - (top - zs[v]) / (top - bottom))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.normal_update()
    return pl.to_object(name, bm, mat)


def fringe(name, centre, normal, radius, depth, mat, level, seed=5):
    """Torn flesh round a severed neck: a ring just below the cut with a jagged lower edge (texture coordinates
    in the stake texture's solid blood near its tip)."""
    rng = np.random.default_rng(seed)
    n = Vector(normal).normalized(); side = n.orthogonal().normalized(); other = n.cross(side)
    seg = (20, 14, 9, 6)[level]
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    top, bottom = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        d = side * math.cos(a) + other * math.sin(a)
        top.append(bm.verts.new(Vector(centre) + d * radius * 0.97 + n * 0.004))
        jag = depth * (0.3 + 0.7 * rng.random() ** 2) if k % 2 == 0 else depth * 0.12
        bottom.append(bm.verts.new(Vector(centre) + d * radius * 1.02 - n * jag))
    for k in range(seg):
        k2 = (k + 1) % seg
        f = bm.faces.new((bottom[k], bottom[k2], top[k2], top[k]))
        for loop in f.loops:
            loop[uv].uv = (0.5, 0.93)
    bm.normal_update()
    return pl.to_object(name, bm, mat)


def eyeball(name, centre, radius, mat, level):
    bm = bmesh.new()
    seg = (12, 8, 6, 4)[level]
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(4, seg // 2 + 1), radius=radius, calc_uvs=True)
    for v in bm.verts:
        v.co += Vector(centre)
    # texture coordinates: the iris (texture centre) on the sphere's -y pole
    uvl = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for loop in f.loops:
            d = (loop.vert.co - Vector(centre)).normalized()
            loop[uvl].uv = (0.5 + 0.5 * d.x, 0.5 + 0.5 * d.z)
    return pl.to_object(name, bm, mat)


def eye_texture(name, iris):
    S = 128
    y, x = np.mgrid[0:S, 0:S] / (S - 1) * 2 - 1
    r = np.hypot(x, y)
    sclera = np.array(lin((190, 170, 160)))
    img = np.broadcast_to(sclera, (S, S, 3)).copy()
    vein = (np.sin(np.arctan2(y, x) * 23) > 0.93) & (r > 0.45)
    img[vein] = lin((150, 40, 35))
    img[r < 0.55] = lin(iris)
    img[r < 0.22] = (0.01, 0.01, 0.01)
    save_png(os.path.join(ll.TEXTURES, f'{name}_basecolor.png'), ct.linear_to_srgb(img))


def wicker_texture(name, colour, gain=(1.0, 1.0, 1.0)):
    """Plaited basket: broad flat splints running diagonally both ways, over two under two, u around and v up;
    tileable (four splints each way per repeat)."""
    S = 256
    y, x = np.mgrid[0:S, 0:S] / S
    n = 4
    p, q = (x + y) * n, (x - y) * n
    fp, fq = p % 1.0, q % 1.0
    over = ((np.floor(p) + np.floor(q)) % 2 == 0)
    splint_p = np.sin(np.pi * fp) ** 0.35                  # rounded splint edges, dark gaps
    splint_q = np.sin(np.pi * fq) ** 0.35
    top = np.where(over, splint_p, splint_q)
    shade = np.where(over, 0.75 + 0.35 * np.cos(np.pi * (fq - 0.5)), 0.75 + 0.35 * np.cos(np.pi * (fp - 0.5)))
    grain = 0.9 + 0.1 * np.sin(np.where(over, q, p) * 40)
    value = np.clip(top * shade * grain, 0.08, 1.3)
    height = top * shade
    base = np.array(lin(colour)) * np.asarray(gain)
    rgb = np.clip(base[None, None, :] * value[..., None], 0, 1)
    save_png(os.path.join(ll.TEXTURES, f'{name}_basecolor.png'), ct.linear_to_srgb(rgb), top_down=False)
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 4.0
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 4.0
    nrm = np.stack([-dx, -dy, np.ones_like(height)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    save_png(os.path.join(ll.TEXTURES, f'{name}_normal.png'), nrm * 0.5 + 0.5, top_down=False)
    mr = np.zeros((S, S, 3)); mr[..., 1] = 0.8
    save_png(os.path.join(ll.TEXTURES, f'{name}_mr.png'), mr)


def basket(name, radius, height, mat, level):
    """Flared plaited bowl with a thick rolled rim (a quarter of the height), flat bottom; the outside carries
    the splints (u around five repeats, v one repeat up the side)."""
    seg = (32, 20, 12, 8)[level]
    r0, h = radius, height
    rim = h * 0.2
    profile = [(0.0, 0.0), (r0 * 0.74, 0.0), (r0 * 0.84, h * 0.3), (r0 * 0.93, h - rim), (r0 * 1.03, h - rim * 0.7),
               (r0 * 1.05, h - rim * 0.3), (r0 * 1.0, h), (r0 * 0.92, h - rim * 0.15), (r0 * 0.88, h - rim),
               (r0 * 0.78, h * 0.35), (0.0, h * 0.08)]
    if level >= 2:
        profile = [(0.0, 0.0), (r0 * 0.74, 0.0), (r0 * 0.93, h - rim), (r0 * 1.05, h - rim * 0.4), (r0 * 0.98, h),
                   (r0 * 0.88, h - rim), (0.0, h * 0.08)]
    return pl.lathe(name, profile, seg, mat, u_repeat=5.0, v_scale=1.0 / (h * 1.1))


def head_build(name, spec, preview=False):
    pl.reset()
    arm, body = cp.load(os.path.join(ll.MODELS, spec['model']))
    rotation = spec.get('rotation', IDENTITY)
    cp.place(arm, rotation, (0, 0, 0))
    run_pose(arm, spec['pose'])
    head, tail = world_head(arm, M + 'Neck'), world_tail(arm, M + 'Neck')
    anchor = head.lerp(tail, spec['cut'])
    hips = Vector(spec['anchor']) - anchor
    cp.place(arm, rotation, hips)
    run_pose(arm, [])
    keep = descendants(arm, M + 'Neck') + [M + 'Spine2', M + 'LeftShoulder', M + 'RightShoulder']
    baked = cp.bake(arm, body, name, drop_groups=('Knife',) + tuple(spec.get('drop', ())), keep_groups=keep)
    mats = {'Body': bpy.data.materials.new('BodyTmp'),
            'Flesh': ll.material('Flesh', 'stake'), 'Stake': ll.material('Stake', 'stake')}
    baked.data.materials.clear(); baked.data.materials.append(mats['Body']); baked.data.materials.append(mats['Flesh'])
    point, normal = neck_cut(baked, arm, spec['cut'], 1)
    cap = [baked.matrix_world @ v.co for v in baked.data.vertices
           if abs((baked.matrix_world @ v.co - point).dot(normal)) < 0.003]
    radii = [(c - point - normal * (c - point).dot(normal)).length for c in cap]
    neck_radius = float(np.median(radii)) if radii else 0.05
    info = {'neck': point, 'normal': normal, 'head': world_head(arm, M + 'Head'), 'neck_radius': neck_radius,
            'top': max((baked.matrix_world @ v.co).z for v in baked.data.vertices)}
    if 'capture' in spec:
        info.update(spec['capture'](arm, baked))
    wounds = [(tuple(point), spec.get('stump_radius', 0.075), spec.get('stump_run', 0.1))]
    for w in spec.get('wounds', []):
        wounds.append((tuple(info['head'] + Vector(w[0])), w[1], w[2]))
    bpy.data.objects.remove(body); bpy.data.objects.remove(arm)
    if preview:
        parts = [baked] + spec['extra'](0, {k: mats['Stake'] for k in ('Stake', 'Hair', 'Eye', 'Basket')}, info)
        pl.setup_render((512, 512))
        paths = pl.render_views(parts, os.path.join(ll.REVIEW, name), 'pose', views=((0, 6), (40, 20), (90, 6)))
        print('PREVIEW', paths, 'BOUNDS', [tuple(round(c, 3) for c in b) for b in pl.bounds(parts)])
        return
    head_texture(name, spec, baked, wounds)
    placeholder = mats['Body']
    mats['Body'] = ll.material('Body', name)
    baked.data.materials[0] = mats['Body']
    bpy.data.materials.remove(placeholder)
    for key, tex in spec.get('materials', {}).items():
        mats[key] = ll.material(key, tex, alpha=key == 'Hair')
    for p in baked.data.polygons:
        p.use_smooth = True
    finish_lods(name, spec, baked, mats, info)


def finish_lods(name, spec, baked, mats, info):
    lods = []
    for level, target in enumerate(spec['levels']):
        copy = baked.copy(); copy.data = baked.data.copy(); bpy.context.scene.collection.objects.link(copy)
        for g in list(copy.vertex_groups):
            copy.vertex_groups.remove(g)
        if 'rest' in copy.data.attributes:
            copy.data.attributes.remove(copy.data.attributes['rest'])
        pl.decimate_to(copy, target)
        cp.clean(copy)
        parts = [copy] + spec['extra'](level, mats, info)
        obj = pl.join(f'{name}{level}', parts)
        occ = dict(rays=(40, 24, 16, 12)[level], distance=0.12, strength=0.55)
        occ.update(spec.get('occlusion', {}))
        o = pl.vertex_occlusion(obj, **occ)
        cc.tint(obj, model_tints(spec, obj))
        title = name.capitalize()
        obj.name = title if level == 0 else f'{title}_LOD{level}'; obj.data.name = obj.name
        print('LEVEL', level, obj.name, 'tris', pl.triangles(obj), 'mean occlusion', round(o, 3))
        lods.append(obj)
    lo, hi = pl.bounds(lods[:1])
    print('BOUNDS', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
    bpy.data.objects.remove(baked)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ll.WORK, f'{name}.blend'))
    pl.export(lods, os.path.join(ll.WORK, f'{name}_export.glb'))


# ---------------------------------------------------------------- bodies
LEG_CLOTH_BONES = (M + 'Hips', M + 'LeftUpLeg', M + 'RightUpLeg', M + 'LeftLeg', M + 'RightLeg')


def body_texture(name, spec, bodies):
    """One recoloured atlas shared by every body of the corpse: corpse_texture.recolour on the first body's
    classes; with `cloth_legs`, the trousers and the tunic below the waist become a neutral light cloth (each
    body's COLOR_0 then tints its legs); blood is the union of every body's wounds rasterised on its own pose."""
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
    names = sorted(set(cp.strongest_bone(bodies[0][0])))
    blood = None
    lin_c = None
    for k, (obj, wounds) in enumerate(bodies):
        strongest = cp.strongest_bone(obj)
        index = np.array([names.index(b) for b in strongest], np.int32)
        pos, bone, rest_z = ct.rasterise(obj, base.size, index)
        covered = (bone >= 0) * 1.0
        pos, bone, rest_z = ct.dilate(pos, bone, rest_z)
        if lin_c is None:
            settings = dict(spec['texture']); settings['tier_mask'] = tier
            lin_c = ct.recolour(rgba[..., :3], bone, names, settings, pos, rest_z)
            src = rgba[..., :3]
            cloth = np.zeros(bone.shape, bool)
            if spec['texture'].get('cloth_legs'):
                bone_name = np.array(names + [''])[bone]
                legs = np.isin(bone_name, LEG_CLOTH_BONES) & (rest_z > spec['texture'].get('shoe_top', 0.12))
                mx = src.max(-1); mn = src.min(-1)
                sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
                skin = (sat > 0.18) & (sat < 0.7) & (mx > 0.5) & (src[..., 0] > src[..., 1]) & ~tier
                cloth = legs & ~skin
                lum = ct.box_blur(ct.srgb_to_linear(src) @ np.array([0.2126, 0.7152, 0.0722]), 6)
                shade = np.clip(lum / float(np.median(lum[cloth])), 0.35, 1.4)[..., None] ** 0.8
                lin_c[cloth] = (np.asarray(spec['texture']['cloth_legs']) * shade)[cloth]
            if spec['texture'].get('tier_skin'):
                # bare torso where the tunic was: the skin colour over heavily smoothed shading (no weave)
                bare = tier & ~cloth & (bone >= 0)
                smooth = ct.box_blur(ct.srgb_to_linear(src) @ np.array([0.2126, 0.7152, 0.0722]), 10)
                shade = np.clip(smooth / float(np.median(smooth[bare])), 0.5, 1.3)[..., None] ** 0.8
                lin_c[bare] = (np.asarray(spec['texture']['pale']) * shade)[bare]
            pos0 = pos
        m = ct.blood_mask(pos, covered, wounds)
        blood = m if blood is None else np.maximum(blood, m)
    lin_c = paint_blood(lin_c, blood, pos0) * texture_gain(spec)
    cc.save_array(os.path.join(ll.TEXTURES, f'{name}_basecolor.png'), ct.linear_to_srgb(lin_c))
    for suffix in ('source', 'mask'):
        os.remove(paths[suffix])
    print('TEXTURE', name, base.size, 'blood', round(float(blood.mean()), 4))


def leg_tint(obj, colour, shoe_top=0.12):
    """Per-vertex trouser tint (linear rgb) in the 'legtint' point attribute (survives decimation): leg-weighted
    vertices above the boot tops (rest height)."""
    strongest = cp.strongest_bone(obj)
    rest = np.zeros(len(obj.data.vertices) * 3, np.float32)
    obj.data.attributes['rest'].data.foreach_get('vector', rest)
    rest_z = rest.reshape(-1, 3)[:, 2]
    attr = obj.data.attributes.new('legtint', 'FLOAT_VECTOR', 'POINT')     # not a colour attribute: COLOR_0
    values = []                                                               # stays the occlusion layer
    for b, z in zip(strongest, rest_z):
        values += list(colour) if b in LEG_CLOTH_BONES and z > shoe_top else [1.0, 1.0, 1.0]
    attr.data.foreach_set('vector', values)


def body_build(name, spec, preview=False):
    pl.reset()
    bodies, infos = [], []
    for k, b in enumerate(spec['bodies']):
        arm, body = cp.load(os.path.join(ll.MODELS, spec['model']))
        cp.place(arm, b['rotation'], b['hips'])
        run_pose(arm, b['pose'])
        baked = cp.bake(arm, body, f'{name}_body{k}', drop_groups=('Knife',))
        wounds = cc.stake_wounds(baked, spec.get('stakes', [])) + cc.bone_wounds(arm, b.get('wounds', []))
        infos.append({'hands': [world_head(arm, M + h) for h in ('LeftHand', 'RightHand')],
                      'feet': [world_head(arm, M + f) for f in ('LeftFoot', 'RightFoot')]})
        bpy.data.objects.remove(body); bpy.data.objects.remove(arm)
        bodies.append((baked, wounds))
    info = {'bodies': infos}
    mats = {'Stake': ll.material('Stake', 'stake'), 'Flesh': ll.material('Flesh', 'stake')}
    if preview:
        wood = bpy.data.materials.new('Preview')
        for k, (b, _) in enumerate(bodies):
            lo, hi = pl.bounds([b])
            print('BODY', k, [round(c, 2) for c in lo], [round(c, 2) for c in hi])
        parts = [b for b, _ in bodies] + spec['extra'](0, {k: wood for k in ('Stake', 'Wood', 'Rope')}, info)
        pl.setup_render((512, 512))
        paths = pl.render_views(parts, os.path.join(ll.REVIEW, name), 'pose', views=((0, 6), (40, 20), (90, 6)))
        print('PREVIEW', paths, 'BOUNDS', [tuple(round(c, 3) for c in b) for b in pl.bounds(parts)])
        return
    body_texture(name, spec, bodies)
    mats['Body'] = ll.material('Body', name)
    for key, tex in spec.get('materials', {}).items():
        mats[key] = ll.material(key, tex)
    for (obj, _), b in zip(bodies, spec['bodies']):
        obj.data.materials.clear(); obj.data.materials.append(mats['Body'])
        for poly in obj.data.polygons:
            poly.use_smooth = True
        leg_tint(obj, b.get('legs', (1.0, 1.0, 1.0)), spec['texture'].get('shoe_top', 0.12) + 0.03)
    lods = []
    for level, target in enumerate(spec['levels']):
        parts = []
        for obj, _ in bodies:
            copy = obj.copy(); copy.data = obj.data.copy(); bpy.context.scene.collection.objects.link(copy)
            for g in list(copy.vertex_groups):
                copy.vertex_groups.remove(g)
            if 'rest' in copy.data.attributes:
                copy.data.attributes.remove(copy.data.attributes['rest'])
            pl.decimate_to(copy, target // len(bodies))
            cp.clean(copy)
            parts.append(copy)
        parts += spec['extra'](level, mats, info)
        for part in parts:
            if 'legtint' not in part.data.attributes:
                attr = part.data.attributes.new('legtint', 'FLOAT_VECTOR', 'POINT')
                attr.data.foreach_set('vector', [1.0] * (3 * len(part.data.vertices)))
        obj = pl.join(f'{name}{level}', parts)
        occ = dict(rays=(40, 24, 16, 12)[level], distance=0.25, strength=0.6)
        occ.update(spec.get('occlusion', {}))
        o = pl.vertex_occlusion(obj, **occ)
        colour = obj.data.color_attributes['Color']; legs = obj.data.attributes['legtint']
        for c, t in zip(colour.data, legs.data):
            v = c.color; w = t.vector
            c.color = (v[0] * w[0], v[1] * w[1], v[2] * w[2], v[3])
        obj.data.attributes.remove(obj.data.attributes['legtint'])
        obj.data.color_attributes.active_color = obj.data.color_attributes['Color']
        cc.tint(obj, model_tints(spec, obj))
        title = name.capitalize()
        obj.name = title if level == 0 else f'{title}_LOD{level}'; obj.data.name = obj.name
        print('LEVEL', level, obj.name, 'tris', pl.triangles(obj), 'mean occlusion', round(o, 3))
        lods.append(obj)
    lo, hi = pl.bounds(lods[:1])
    print('BOUNDS', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
    for obj, _ in bodies:
        bpy.data.objects.remove(obj)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ll.WORK, f'{name}.blend'))
    pl.export(lods, os.path.join(ll.WORK, f'{name}_export.glb'))


def pole(name, a, b, radius, sides, mat):
    return pl.tube(name, a, b, radius, radius * 0.9, sides, mat, v_scale=1.2, caps=True)


BAR_Z = 1.0
BAR_X = (-1.04, 0.83)
FRAMES = (-0.93, 0.76)


def c02_extra(level, mats, info):
    """The rack: a crossbar between two A-frames of crossed poles (lashed where they cross under the bar), and
    rope bindings round the bar at the ankles and the wrists."""
    sides = (8, 6, 5, 4)[level]
    parts = [pole(f'bar{level}', (BAR_X[0], 0, BAR_Z), (BAR_X[1], 0, BAR_Z), 0.026, sides, mats['Wood'])]
    for k, x in enumerate(FRAMES):
        for s in (-1, 1):
            parts.append(pole(f'leg{level}_{k}{s}', (x - 0.1 * s, 0.28 * s, 0.012), (x + 0.035 * s, -0.04 * s, 1.13),
                              0.028, sides, mats['Wood']))
        if level < 3:
            parts.append(hp.coil(f'lash{level}_{k}', (x, 0, BAR_Z - 0.06), (x, 0, BAR_Z + 0.03), 0.034, 0.008, 2.5,
                                 (5, 4, 3)[level], mats['Rope'], ring_sides=(8, 6, 5)[level]))
    if level < 3:
        body = info['bodies'][0]
        for p, kind in ((sum(body['feet'], Vector()) / 2, 'ankles'), (sum(body['hands'], Vector()) / 2, 'wrists')):
            a = Vector((p.x - 0.035, 0, BAR_Z)); b = Vector((p.x + 0.035, 0, BAR_Z))
            parts.append(hp.coil(f'{kind}{level}', a, b, 0.036, 0.008, 3.0, (5, 4, 3)[level], mats['Rope'],
                                 ring_sides=(8, 6, 5)[level]))
    return parts


SUPINE_RIGHT = rot('Z', -90) @ rot('X', -90)
SUPINE_LEFT = rot('Z', 90) @ rot('X', -90)
PRONE_RIGHT = rot('Z', 90) @ rot('X', 90)
POLE_TOP = 2.2


def c03_extra(level, mats, info):
    """The pole all three bodies are run through (bloody upper third, a long point at the top)."""
    return [cc.stake(f'pole{level}', (0, 0, 0), (0, 0, POLE_TOP), 0.016, cc.STAKE_SIDES[level], mats['Stake'], 3)]
LEFT_ANKLE, RIGHT_ANKLE = (-0.72, 0.04, BAR_Z + 0.03), (-0.66, -0.04, BAR_Z + 0.03)
LEFT_WRIST, RIGHT_WRIST = (0.0, 0.04, BAR_Z + 0.03), (0.07, -0.04, BAR_Z + 0.03)


def texture_gain(spec):
    return np.array([max(a, 1.0) for a in spec.get('albedo', (1.0, 1.0, 1.0))])


def model_tints(spec, obj):
    """Per-material COLOR_0 tints: spec 'tints' times the darkening part of the whole-model 'albedo' multiplier
    (linear(native sprite mean) / linear(flat front albedo), measured with suggest_tints.py) on every material.
    COLOR_0 cannot brighten (it is stored normalised, clamped at 1), so the brightening part goes into the
    model's own textures instead (texture_gain)."""
    whole = [min(a, 1.0) for a in spec.get('albedo', (1.0, 1.0, 1.0))]
    out = {}
    for m in obj.data.materials:
        key = m.name.split('.')[0]
        t = spec.get('tints', {}).get(key, (1.0, 1.0, 1.0))
        out[key] = tuple(a * b for a, b in zip(t, whole))
    return out


# ---------------------------------------------------------------- per-corpse props
def c09_extra(level, mats, info):
    """A pointed stake from the ground up into the neck stump (tip hidden inside the head)."""
    tip = info['neck'] + Vector((0, 0, 0.09))
    return [cc.stake(f'stake{level}', (0, 0, 0), tuple(tip), 0.016, cc.STAKE_SIDES[level], mats['Stake'], 1),
            fringe(f'fringe{level}', info['neck'], info['normal'], info['neck_radius'], 0.04, mats['Flesh'], level)]


def c10_extra(level, mats, info):
    """The spike runs from the ground up through the neck and out of the crown; the long hair falls round it."""
    head = info['head']
    parts = [cc.stake(f'stake{level}', (0, 0, 0), (0.0, head.y + 0.005, info['top'] + 0.105), 0.0125,
                      cc.STAKE_SIDES[level], mats['Stake'], 2),
             hair_curtain(f'hair{level}', info['skull_centre'], info['skull_radius'] * 1.05, info['top'] + 0.02,
                          info['eye_socket'].z + 0.05, info['neck'].z - 0.15, 0.03, 100, mats['Hair'], level),
             fringe(f'fringe{level}', info['neck'], info['normal'], info['neck_radius'], 0.035, mats['Flesh'],
                    level)]
    if level < 3:
        parts.append(eyeball(f'eye{level}', tuple(info['eye']), 0.011, mats['Eye'], level))
    return parts


def c10_capture(arm, baked):
    """The left eye (screen right): the front-most head vertices right of centre at eye height, the eyeball hung
    out on the cheek below it; the skull's centre and radius above the eyes."""
    head = world_head(arm, M + 'Head')
    best = None
    pts = [baked.matrix_world @ v.co for v in baked.data.vertices]
    for p in pts:
        if 0.02 < p.x - head.x < 0.05 and 0.06 < p.z - head.z < 0.10:
            if best is None or p.y < best.y:
                best = p.copy()
    skull = [p for p in pts if p.z > best.z + 0.02]
    xs = [p.x for p in skull]; ys = [p.y for p in skull]
    centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    radius = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
    return {'eye': best + Vector((0.008, -0.008, -0.032)), 'skull_centre': centre, 'skull_radius': radius,
            'eye_socket': best}


def c01_extra(level, mats, info):
    return [basket(f'basket{level}', 0.185, 0.16, mats['Basket'], level),
            fringe(f'fringe{level}', info['neck'], info['normal'], info['neck_radius'], 0.03, mats['Flesh'], level)]


HEAD_LEVELS = (5200, 2200, 800, 260)
CORPSES = {
    # Bearded man's head (the pmn2 mage: dark long hair and full beard) on a pointed stake, slightly turned and
    # tilted; the stump soaked, blood running down the stake. Sprite 102 units: head about half the height.
    'corpse09': {
        'albedo': (1.152, 1.098, 1.326),  # flat front albedo -> sprite mean (suggest_tints.py)
        'kind': 'head', 'model': 'mm6_pmn2.glb', 'cut': 0.45, 'anchor': (0.0, 0.0, 0.26),
        'pose': [('rot', M + 'Neck', (0, 0, 1), 8), ('rot', M + 'Neck', (1, 0, 0), -6)],
        'extra': c09_extra, 'levels': (2800, 1300, 520, 200),
        'tints': {'Stake': (0.55, 0.75, 0.65)},              # sprite stake (82, 57, 36) over the stake texture
        'wounds': [((0.03, -0.09, 0.07), 0.01, 0.04), ((-0.04, -0.08, 0.12), 0.008, 0.03)],
        'texture': {'skin': lin((128, 76, 48)), 'hair': lin((42, 31, 25)), 'bruise': 0.3},
    },
    # Long-haired woman's head (pfem face) on a spike out through the crown; her loose brown hair hangs round the
    # stake as a curtain to well below the neck; her left eye hangs out on the cheek. Sprite 127 units.
    'corpse10': {
        'albedo': (0.708, 0.84, 1.031),  # flat front albedo -> sprite mean (suggest_tints.py)
        'kind': 'head', 'model': 'mm6_pfem.glb', 'cut': 0.5, 'anchor': (0.0, 0.0, 0.22),
        'pose': [('rot', M + 'Neck', (0, 0, 1), -6), ('rot', M + 'Neck', (0, 1, 0), 5)],
        'tints': {'Stake': (0.35, 0.28, 0.22)},              # the sprite's dark, blood-soaked spike (44, 21, 6)
        'capture': c10_capture, 'extra': c10_extra, 'drop': ('Braid_1', 'Braid_2', 'Braid_3'),
        'levels': (4400, 1900, 700, 190),
        'materials': {'Hair': 'corpse10_hair', 'Eye': 'corpse10_eye'},
        'wounds': [((0.0, -0.05, 0.19), 0.014, 0.12), ((0.035, -0.08, 0.075), 0.014, 0.07),
                   ((0.0, -0.09, 0.0), 0.01, 0.05)],
        'texture': {'skin': lin((156, 102, 84)), 'hair': lin((104, 60, 46)), 'bruise': 0.15},
    },
    # Old man's head (pmn2 with white hair and beard) lying on its side in a wicker basket, face to the viewer,
    # crown to the right. Sprite 47 units.
    'corpse01': {
        'albedo': (1.419, 1.35, 1.38),  # flat front albedo -> sprite mean (suggest_tints.py)
        'kind': 'head', 'model': 'mm6_pmn2.glb', 'cut': 0.45, 'anchor': (-0.13, -0.02, 0.15),
        'rotation': rot('Y', 76) @ rot('X', 12),
        'pose': [('rot', M + 'Neck', (0, 0, 1), 10)],
        'extra': c01_extra, 'levels': (3300, 1500, 600, 180), 'materials': {'Basket': 'corpse01_wicker'},
        'wounds': [((0.0, -0.09, 0.08), 0.03, 0.05), ((0.04, -0.08, 0.04), 0.02, 0.04)],
        'texture': {'skin': lin((150, 94, 82)), 'hair': lin((84, 76, 72)), 'bruise': 0.2},
    },
    # Hung under a rack by the wrists and ankles, like carried game: feet and hands bound to the crossbar, the
    # back sagging, hips lowest, the head hanging back to the right. Bare, pale, bloodied belly and chest.
    # Sprite 128 units (2.2 m wide, 1.3 m tall here).
    'corpse02': {
        'albedo': (0.719, 0.68, 0.641),  # flat front albedo -> sprite mean (suggest_tints.py)
        'kind': 'body', 'model': 'mm6_pman.glb', 'levels': (4700, 2100, 760, 220),
        'materials': {'Wood': 'wood', 'Rope': 'rope'},
        # sprite poles (55, 32, 22) and bindings (100, 70, 40) sRGB over the wood / rope texture means
        'tints': {'Wood': (0.33, 0.35, 0.37), 'Rope': (0.56, 0.43, 0.33)},
        'bodies': [{
            'rotation': roll(35) @ SUPINE_RIGHT, 'hips': (-0.16, 0.0, 0.40),
            'pose': [
                ('aim', M + 'Spine', (1, 0, 0.95), 1.0), ('aim', M + 'Spine1', (1, 0, 0.6), 1.0),
                ('aim', M + 'Spine2', (1, 0, 0.35), 1.0),
                ('aim', M + 'Neck', (1, -0.1, -0.35), 1.0), ('aim', M + 'Head', (0.8, -0.35, -0.9), 1.0),
                ('reach', M + 'LeftUpLeg', M + 'LeftLeg', M + 'LeftFoot', LEFT_ANKLE, (-0.3, 0, -1)),
                ('reach', M + 'RightUpLeg', M + 'RightLeg', M + 'RightFoot', RIGHT_ANKLE, (-0.3, 0, -1)),
                ('aim', M + 'LeftFoot', (0.25, 0.1, 1), 1.0), ('aim', M + 'RightFoot', (0.15, -0.1, 1), 1.0),
                ('reach', M + 'LeftArm', M + 'LeftForeArm', M + 'LeftHand', LEFT_WRIST, (1, 0, 0)),
                ('reach', M + 'RightArm', M + 'RightForeArm', M + 'RightHand', RIGHT_WRIST, (1, 0, 0)),
                ('aim', M + 'LeftHand', (0, 0.1, 1), 1.0), ('aim', M + 'RightHand', (0, -0.1, 1), 1.0),
            ],
            'wounds': [(M + 'Spine', 0.5, 0.2, 0.3), (M + 'Spine1', 0.6, 0.18, 0.25), (M + 'Hips', 0.5, 0.16, 0.25),
                       (M + 'Spine2', 0.5, 0.14, 0.2), (M + 'Neck', 0.6, 0.07, 0.15), (M + 'Head', 0.4, 0.05, 0.1),
                       (M + 'LeftUpLeg', 0.3, 0.06, 0.1)],
        }],
        'extra': c02_extra,
        'texture': {'pale': lin((132, 80, 60)), 'tier_skin': True, 'pale_cloth': True,
                    'pale_leather': True, 'hair': (0.02, 0.012, 0.008)},
    },
    # Three peasants run through by one tall pole, one above another (2.2 m): the top one on his back, chest to
    # the viewer, head to the right, knees bent (blue trousers); the middle one face down, folded over the pole at
    # the waist, torso and arms hanging right, legs left (red); the bottom one arched backward over it, head hanging
    # left, legs right (green). Shirtless, knee boots. One shared texture, the trousers tinted per body in COLOR_0.
    # Sprite 165 units.
    'corpse03': {
        'albedo': (0.591, 0.6, 0.645),  # flat front albedo -> sprite mean (suggest_tints.py)
        'kind': 'body', 'model': 'mm6_pman.glb', 'levels': (5700, 2400, 870, 290),
        'stakes': [((0, 0, 0), (0, 0, POLE_TOP), 0.016)],
        'tints': {'Stake': (0.55, 0.6, 0.6)},
        'bodies': [
            {'rotation': roll(60) @ SUPINE_RIGHT, 'hips': (-0.19, 0.0, 1.72), 'legs': (0.11, 0.11, 0.21),
             'pose': [
                 ('aim', M + 'Spine', (1, 0, 0.35), 1.0), ('aim', M + 'Spine1', (1, 0, 0.3), 1.0),
                 ('aim', M + 'Spine2', (1, 0, 0.15), 1.0), ('aim', M + 'Neck', (1, -0.2, -0.2), 1.0),
                 ('aim', M + 'Head', (0.7, -0.4, -0.6), 1.0),
                 ('aim', M + 'LeftUpLeg', (-1, 0.12, 0.15), 1.0), ('aim', M + 'RightUpLeg', (-1, -0.12, -0.25), 1.0),
                 ('aim', M + 'LeftLeg', (-0.6, 0.1, -0.8), 1.0), ('aim', M + 'RightLeg', (-0.45, -0.1, -0.85), 1.0),
                 ('aim', M + 'LeftArm', (0.25, 0.5, -1), 1.0), ('aim', M + 'LeftForeArm', (0.1, 0.3, -1), 1.0),
                 ('aim', M + 'RightArm', (0.1, -0.35, -1), 1.0), ('aim', M + 'RightForeArm', (-0.1, -0.2, -1), 1.0),
             ],
             'wounds': [(M + 'Spine1', 0.5, 0.06, 0.15), (M + 'Neck', 0.5, 0.05, 0.12)]},
            {'rotation': roll(-25) @ PRONE_RIGHT, 'hips': (-0.02, 0.0, 1.38), 'legs': (0.17, 0.04, 0.018),
             'pose': [
                 ('aim', M + 'Spine', (1, 0, -0.2), 1.0), ('aim', M + 'Spine1', (1, 0, -0.6), 1.0),
                 ('aim', M + 'Spine2', (0.8, 0, -1), 1.0), ('aim', M + 'Neck', (0.3, -0.1, -1), 1.0),
                 ('aim', M + 'Head', (0.0, -0.2, -1), 1.0),
                 ('aim', M + 'LeftArm', (0.1, 0.25, -1), 1.0), ('aim', M + 'LeftForeArm', (0, 0.1, -1), 1.0),
                 ('aim', M + 'RightArm', (0.15, -0.3, -1), 1.0), ('aim', M + 'RightForeArm', (0, -0.1, -1), 1.0),
                 ('aim', M + 'LeftUpLeg', (-1, 0.12, -0.4), 1.0), ('aim', M + 'RightUpLeg', (-1, -0.12, -0.3), 1.0),
                 ('aim', M + 'LeftLeg', (-0.35, 0.05, -1), 1.0), ('aim', M + 'RightLeg', (-0.2, -0.05, -1), 1.0),
             ],
             'wounds': [(M + 'Spine', 0.4, 0.07, 0.2), (M + 'Head', 0.5, 0.05, 0.12)]},
            {'rotation': roll(50) @ SUPINE_LEFT, 'hips': (0.18, 0.0, 0.72), 'legs': (0.08, 0.14, 0.08),
             'pose': [
                 ('aim', M + 'Spine', (-1, 0, 0.4), 1.0), ('aim', M + 'Spine1', (-1, 0, 0.0), 1.0),
                 ('aim', M + 'Spine2', (-1, 0, -0.45), 1.0), ('aim', M + 'Neck', (-0.5, -0.1, -1), 1.0),
                 ('aim', M + 'Head', (-0.3, -0.3, -1), 1.0),
                 ('aim', M + 'LeftArm', (-0.2, 0.3, -1), 1.0), ('aim', M + 'LeftForeArm', (-0.1, 0.2, -1), 1.0),
                 ('aim', M + 'RightArm', (-0.4, -0.4, -1), 1.0), ('aim', M + 'RightForeArm', (-1, -0.3, 0.2), 1.0),
                 ('aim', M + 'LeftUpLeg', (1, 0.1, -0.4), 1.0), ('aim', M + 'LeftLeg', (0.2, 0.0, -1), 1.0),
                 ('aim', M + 'RightUpLeg', (0.9, -0.15, -0.5), 1.0), ('aim', M + 'RightLeg', (-0.7, -0.05, -0.7), 1.0),
             ],
             'wounds': [(M + 'Spine2', 0.5, 0.06, 0.15), (M + 'Head', 0.5, 0.05, 0.1)]},
        ],
        'extra': c03_extra,
        'texture': {'pale': lin((150, 100, 88)), 'tier': lin((150, 98, 84)), 'feet': (0.04, 0.009, 0.0035),
                    'shoe_top': 0.38, 'cloth_legs': (0.5, 0.5, 0.5), 'tier_skin': True},
    },
}


def prepare_textures(name):
    if name == 'corpse10':
        hair_texture('corpse10_hair', (112, 64, 48))
        eye_texture('corpse10_eye', (30, 120, 90))
    if name == 'corpse01':
        wicker_texture('corpse01_wicker', (84, 50, 21), texture_gain(CORPSES[name]))


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    name = args[0]
    spec = CORPSES[name]
    prepare_textures(name)
    if spec['kind'] == 'head':
        head_build(name, spec, preview='--preview' in args)
    else:
        body_build(name, spec, preview='--preview' in args)
