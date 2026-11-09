"""Impaled corpses `corpse04`, `corpse05`, `corpse06`, `corpse16`: an MM6 peasant (mm6_pfem.glb / mm6_pman.glb, read
only) posed with world-space bone operations (corpse_pose.py) into the sprite's pose, baked static and welded, run
through by sharpened bloody stakes (`stake` texture). Stakes are given as lines or `impale` entries (through a point
of a posed bone, so they always pierce the body); wounds are where the stakes enter and leave the body plus listed
bone points. The body texture is a recoloured, bloodied copy of the peasant's atlas (corpse_texture.py), with
unchanged copies of its normal and metal/roughness maps; corpse16 keeps only the legs, cut square across mid-thigh
with flesh caps. Each LOD is the welded body collapse-decimated to LEVELS plus its stakes, vertex occlusion in
COLOR_0. Writes textures/<corpse>_{basecolor,normal,mr}.png and work/<corpse>_export.glb.
Usage: blender --background --python build_corpse.py -- <corpse> [--preview]
--preview renders the posed body and stakes only (review/<corpse>/pose_*.png)."""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl
import corpse_pose as cp
import corpse_texture as ct

MODELS = os.path.join(pl.REPO, 'assets_dev', 'worlds', 'mm6', 'models')
SUPINE_LEFT = Matrix.Rotation(math.radians(90), 3, 'Z') @ Matrix.Rotation(math.radians(-90), 3, 'X')
PRONE_RIGHT = Matrix.Rotation(math.radians(90), 3, 'Z') @ Matrix.Rotation(math.radians(90), 3, 'X')
LEG_BONES = tuple(f'mixamorig:{side}{part}' for side in ('Left', 'Right')
                  for part in ('UpLeg', 'Leg', 'Foot', 'ToeBase'))


def roll(degrees):
    return Matrix.Rotation(math.radians(degrees), 3, 'X')


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


CORPSES = {
    # Folded backward over one stake through the pelvis: torso and head hang to the left, the skirt and legs to
    # the right; near (right) arm hangs straight down, far arm reaches out past the head. Sprite 177 units.
    'corpse04': {
        'model': 'mm6_pfem.glb', 'height': 1.59,
        'rotation': roll(45) @ SUPINE_LEFT, 'hips': (0.06, 0.0, 1.22),
        'pose': [
            ('aim', 'mixamorig:Spine', (-1, 0, -0.25), 1.0),
            ('aim', 'mixamorig:Spine1', (-1, 0, -0.55), 1.0),
            ('aim', 'mixamorig:Spine2', (-1, 0, -0.9), 1.0),
            ('aim', 'mixamorig:Neck', (-0.6, 0, -1), 1.0),
            ('aim', 'mixamorig:Head', (-0.35, -0.2, -1), 1.0),
            ('aim', 'mixamorig:LeftUpLeg', (0.25, 0.05, -1), 1.0),
            ('aim', 'mixamorig:RightUpLeg', (0.25, -0.05, -1), 1.0),
            ('aim', 'mixamorig:LeftLeg', (0.2, 0.05, -1), 1.0),
            ('aim', 'mixamorig:RightLeg', (0.3, -0.05, -1), 1.0),
            ('aim', 'mixamorig:RightArm', (0.15, -0.2, -1), 1.0),
            ('aim', 'mixamorig:RightForeArm', (0.05, -0.1, -1), 1.0, 'mixamorig:RightHand'),
            ('aim', 'mixamorig:LeftArm', (-1, 0.25, -0.5), 1.0),
            ('aim', 'mixamorig:LeftForeArm', (-1, 0.1, -0.2), 1.0, 'mixamorig:LeftHand'),
            ('aim', 'Braid_1', (0, 0, -1), 1.0), ('aim', 'Braid_2', (0, 0, -1), 1.0),
            ('aim', 'Braid_3', (0, 0, -1), 1.0),
        ] + skirt_down((0.25, 0, -1), tatter=14),
        'stakes': [((0.0, 0.02, 0.0), (0.0, 0.0, 1.59), 0.032)],
        'impale': [],
        'wounds': [('mixamorig:Hips', 0.5, 0.16, 0.35), ('mixamorig:Spine', 0.5, 0.10, 0.3),
                   ('mixamorig:Neck', 0.5, 0.06, 0.12), ('mixamorig:Head', 0.35, 0.05, 0.1),
                   ('mixamorig:LeftLeg', 0.85, 0.07, 0.15), ('mixamorig:RightLeg', 0.75, 0.08, 0.2),
                   ('mixamorig:RightForeArm', 0.5, 0.05, 0.15, 'mixamorig:RightHand')],
        'texture': {'hair': (0.30, 0.035, 0.008), 'tier': (0.02, 0.03, 0.075), 'cloth': (0.40, 0.40, 0.42),
                    'cloth_dirt': 0.55},
    },
    # Supine across four thin stakes, arched: chest up toward the camera, head hanging to the left with the far
    # arm beside it, the near arm hanging to the ground; near thigh raised with the shin down, far leg out with the
    # shin hanging. Armour scraps: the tunic as blue-grey steel. Sprite 139 units.
    'corpse05': {
        'model': 'mm6_pman.glb', 'height': 1.25,
        'rotation': roll(55) @ SUPINE_LEFT, 'hips': (0.06, 0.0, 0.73),
        'pose': [
            ('aim', 'mixamorig:Spine', (-1, 0, 0.15), 1.0),
            ('aim', 'mixamorig:Spine1', (-1, 0, 0.05), 1.0),
            ('aim', 'mixamorig:Spine2', (-1, 0, -0.3), 1.0),
            ('aim', 'mixamorig:Neck', (-0.7, 0, -1), 1.0),
            ('aim', 'mixamorig:Head', (-0.45, -0.25, -1), 1.0),
            ('aim', 'mixamorig:RightUpLeg', (0.2, -0.15, 1), 1.0),
            ('aim', 'mixamorig:RightLeg', (0.6, -0.05, -0.75), 1.0),
            ('aim', 'mixamorig:LeftUpLeg', (1, 0.2, 0.3), 1.0),
            ('aim', 'mixamorig:LeftLeg', (0.35, 0.1, -1), 1.0),
            ('aim', 'mixamorig:RightArm', (0.55, -0.3, -1), 1.0),
            ('aim', 'mixamorig:RightForeArm', (0.3, -0.1, -1), 1.0, 'mixamorig:RightHand'),
            ('aim', 'mixamorig:LeftArm', (-0.25, 0.2, -1), 1.0),
            ('aim', 'mixamorig:LeftForeArm', (-0.1, 0.1, -1), 1.0, 'mixamorig:LeftHand'),
        ],
        'stakes': [],
        'impale': [('mixamorig:Neck', 0.0, (0.25, 0.0, 1), 0.92, 0.022),
                   ('mixamorig:Spine2', 0.4, (0.05, 0.05, 1), 1.03, 0.022),
                   ('mixamorig:RightUpLeg', 0.75, (0.05, 0.05, 1), 1.25, 0.024),
                   ('mixamorig:LeftUpLeg', 0.8, (0.25, 0.0, 1), 0.95, 0.022)],
        'wounds': [('mixamorig:Spine', 0.5, 0.07, 0.15), ('mixamorig:Neck', 0.6, 0.05, 0.1),
                   ('mixamorig:Head', 0.3, 0.05, 0.1), ('mixamorig:RightUpLeg', 0.4, 0.05, 0.15),
                   ('mixamorig:LeftLeg', 0.3, 0.04, 0.1)],
        'texture': {'hair': (0.012, 0.011, 0.014), 'tier': (0.05, 0.065, 0.11), 'pale_cloth': True,
                    'feet': (0.05, 0.025, 0.012)},
    },
    # Prone, rolled toward the camera, held up by seven slanting stakes: head raised at the right, the far arm out
    # to the right, the near arm hanging to the ground, legs out behind with the knees bent. Brown mail tunic,
    # red boots. Sprite 128 units.
    'corpse06': {
        'model': 'mm6_pman.glb', 'height': 1.15,
        'rotation': roll(-45) @ PRONE_RIGHT, 'hips': (0.12, 0.0, 0.75),
        'pose': [
            ('aim', 'mixamorig:Spine', (1, 0, 0.05), 1.0),
            ('aim', 'mixamorig:Spine1', (1, 0, 0.0), 1.0),
            ('aim', 'mixamorig:Spine2', (1, 0, 0.1), 1.0),
            ('aim', 'mixamorig:Neck', (0.6, -0.3, 0.8), 1.0),
            ('aim', 'mixamorig:Head', (0.3, -0.4, 1), 1.0),
            ('aim', 'mixamorig:RightUpLeg', (-1, -0.1, 0.0), 1.0),
            ('aim', 'mixamorig:RightLeg', (-0.7, 0, 0.75), 1.0),
            ('aim', 'mixamorig:LeftUpLeg', (-1, 0.15, -0.35), 1.0),
            ('aim', 'mixamorig:LeftLeg', (-0.75, 0.05, 0.6), 1.0),
            ('aim', 'mixamorig:RightArm', (-0.3, -0.3, -1), 1.0),
            ('aim', 'mixamorig:RightForeArm', (0.3, -0.2, -1), 1.0, 'mixamorig:RightHand'),
            ('aim', 'mixamorig:LeftArm', (0.8, 0.1, -0.35), 1.0),
            ('aim', 'mixamorig:LeftForeArm', (0.5, -0.1, -0.85), 1.0, 'mixamorig:LeftHand'),
        ],
        'stakes': [],
        'impale': [('mixamorig:RightLeg', 0.7, (0.35, 0.0, 1), 1.20, 0.02),
                   ('mixamorig:RightUpLeg', 0.6, (0.0, 0.05, 1), 1.08, 0.02),
                   ('mixamorig:LeftUpLeg', 0.5, (-0.1, 0.05, 1), 0.92, 0.02),
                   ('mixamorig:Hips', 0.5, (-0.4, 0.0, 1), 1.12, 0.022),
                   ('mixamorig:Spine2', 0.7, (0.3, 0.0, 1), 1.10, 0.022),
                   ('mixamorig:Neck', 0.5, (-0.05, 0.0, 1), 1.18, 0.02),
                   ('mixamorig:LeftArm', 0.8, (-0.3, 0.0, 1), 1.0, 0.02)],
        'wounds': [('mixamorig:Head', 0.4, 0.06, 0.12), ('mixamorig:Head', 0.75, 0.05, 0.15),
                   ('mixamorig:Neck', 0.5, 0.06, 0.15), ('mixamorig:Spine1', 0.5, 0.07, 0.2)],
        'texture': {'tier': (0.06, 0.035, 0.018), 'pale_cloth': True, 'feet': (0.26, 0.02, 0.01)},
    },
    # Two severed legs on one stake: one through its thigh stump high up, the thigh out to the left and the shin
    # hanging; the other lower, run through above the knee, the shin hanging to the right. Bare and bloodless,
    # stumps soaked. Sprite 139 units.
    'corpse16': {
        'model': 'mm6_pman.glb', 'height': 1.25, 'keep': LEG_BONES,
        'stumps': [('mixamorig:LeftUpLeg', 0.5), ('mixamorig:RightUpLeg', 0.5)], 'levels': (1200, 650, 320, 140),
        'rotation': Matrix.Identity(3), 'hips': (0.0, 0.0, 0.884),
        'pose': [
            ('move', 'mixamorig:LeftUpLeg', (0.19, 0.0, 0.83)),
            ('aim', 'mixamorig:LeftUpLeg', (-1, 0, 0.25), 1.0),
            ('aim', 'mixamorig:LeftLeg', (-0.45, 0, -1), 1.0),
            ('move', 'mixamorig:RightUpLeg', (-0.29, 0.0, 0.50)),
            ('aim', 'mixamorig:RightUpLeg', (1, 0, -0.1), 1.0),
            ('aim', 'mixamorig:RightLeg', (0.5, 0, -1), 1.0),
        ],
        'stakes': [((0.0, 0.0, 0.0), (0.0, 0.0, 1.25), 0.028)],
        'wounds': [('mixamorig:LeftUpLeg', 0.5, 0.14, 0.35), ('mixamorig:RightUpLeg', 0.5, 0.13, 0.3),
                   ('mixamorig:LeftUpLeg', 0.6, 0.04, 0.1)],
        'texture': {'pale_cloth': True, 'pale_leather': True},
    },
}


def stake_preview(name, base, tip, radius, mat):
    return pl.tube(name, base, tip, radius, radius * 0.15, 8, mat, caps=True)


def preview(name, spec):
    pl.reset()
    arm, body = cp.load(os.path.join(MODELS, spec['model']))
    cp.place(arm, spec['rotation'], spec['hips'])
    cp.pose(arm, spec['pose'])
    baked = cp.bake(arm, body, name, drop_groups=('Knife',), keep_groups=spec.get('keep'))
    lines = spec['stakes'] + impale(arm, spec.get('impale', []))
    bpy.data.objects.remove(body); bpy.data.objects.remove(arm)
    wood = bpy.data.materials.new('Stake'); wood.diffuse_color = (0.3, 0.1, 0.05, 1)
    stakes = [stake_preview(f'stake{i}', *s, wood) for i, s in enumerate(lines)]
    lo, hi = pl.bounds([baked] + stakes)
    print('BOUNDS', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
    out = os.path.join(pl.PROPS, 'review', name); os.makedirs(out, exist_ok=True)
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
    pl.reset()
    arm, body = cp.load(os.path.join(MODELS, spec['model']))
    cp.place(arm, spec['rotation'], spec['hips'])
    cp.pose(arm, spec['pose'])
    baked = cp.bake(arm, body, name, drop_groups=('Knife',), keep_groups=spec.get('keep'))
    spec = dict(spec, stakes=spec['stakes'] + impale(arm, spec.get('impale', [])))
    wounds = stake_wounds(baked, spec['stakes']) + bone_wounds(arm, spec.get('wounds', []))
    cuts = stump_cuts(arm, spec.get('stumps', []))
    bpy.data.objects.remove(body); bpy.data.objects.remove(arm)
    texture(name, spec, baked, wounds)
    mats = {'Body': pl.material('Body', name), 'Stake': pl.material('Stake', 'stake'),
            'Flesh': pl.material('Flesh', 'stake')}
    baked.data.materials.clear(); baked.data.materials.append(mats['Body'])
    if cuts:
        seal_stumps(baked, spec, mats['Flesh'], cuts)
    for p in baked.data.polygons:
        p.use_smooth = True
    lods = []
    for level, target in enumerate(spec.get('levels', LEVELS)):
        copy = baked.copy(); copy.data = baked.data.copy(); bpy.context.scene.collection.objects.link(copy)
        for g in list(copy.vertex_groups):
            copy.vertex_groups.remove(g)
        if 'rest' in copy.data.attributes:
            copy.data.attributes.remove(copy.data.attributes['rest'])
        pl.decimate_to(copy, target)
        cp.clean(copy)
        stakes = [stake(f'stake{level}_{i}', *s, STAKE_SIDES[level], mats['Stake'], i) for i, s in
                  enumerate(spec['stakes'])]
        obj = pl.join(f'{name}{level}', [copy] + stakes)
        occl = pl.vertex_occlusion(obj, rays=(40, 24, 16, 12)[level], distance=0.25, strength=0.6)
        title = name.capitalize()
        obj.name = title if level == 0 else f'{title}_LOD{level}'; obj.data.name = obj.name
        print('LEVEL', level, obj.name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3))
        lods.append(obj)
    lo, hi = pl.bounds(lods[:1])
    print('BOUNDS', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
    bpy.data.objects.remove(baked)
    work = os.path.join(pl.PROPS, 'work')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, f'{name}.blend'))
    pl.export(lods, os.path.join(work, f'{name}_export.glb'))


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    if '--preview' in args:
        preview(args[0], CORPSES[args[0]])
    else:
        build(args[0], CORPSES[args[0]])
