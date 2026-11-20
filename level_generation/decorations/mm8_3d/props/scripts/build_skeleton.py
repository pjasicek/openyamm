"""Skeleton lying on the ground `dec05` -> work/skeleton_export.glb (LOD0..3).

The project's MM6 skeleton creature (assets_source/worlds/mm6/models/mm6_ske.glb, read only: 78 rigid bone pieces
plus a skull with separate teeth and jaw, each piece 100 % on one mixamorig joint) is imported, its clips dropped,
laid on its back rolled toward the viewer (head toward -x) and posed with world-space bone operations (MM6 props
corpse_pose.py) into the sprite's compact curled heap: back curled, skull tucked against the ribs facing the viewer,
the near arm folded over the chest, the far arm folded in with its hand on the ground before the ribs, both knees
drawn up toward the chest with the shins folded down to the feet at the right. The pose
is baked static and welded; the red eye swatches are dropped; the ribcage and skull are enlarged and the long bones
thickened toward the sprite's proportions. LOD0 decimates each bone on its own (no bone collapses to a shard); LOD1
is the creature's own LOD2 mesh posed the same way, LOD2 decimates it per bone (further levels shatter into
shards, so three levels). Textures: skeleton_* (make_textures.py).
Usage: blender --background --python build_skeleton.py -- [--preview]"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl, cp = ml.pl, ml.cp
SOURCE = os.path.join(ml.REPO, 'assets_source', 'worlds', 'mm6', 'models', 'mm6_ske.glb')
M = 'mixamorig:'
# Curled up on its back, rolled toward the viewer (rev 2 after the coordinator's review: the sprite is a dense,
# compact heap). Head toward -x, face up, the right side toward the camera at -y:
# rest left (+x) -> +y, rest back (+y) -> -z, rest up (+z) -> -x.
SIDE = Matrix(((0, 0, -1), (1, 0, 0), (0, -1, 0)))
POSE = [('rot', M + 'Hips', (1, 0, 0), 18)]                  # rolled a little toward the viewer
# Joint targets traced on the dec05 x2 sprite (508 x 262 px): (bone, sprite x, sprite y, depth in m; - toward the
# viewer). Each bone is aimed at the point its tail should reach, in order, so parents settle first.
PX = 0.0021                                                   # metres per sprite pixel
TRACE = [
    ('Spine', 250, 182, 0.0), ('Spine1', 180, 186, 0.0), ('Spine2', 110, 176, 0.0),
    ('Neck', 78, 196, -0.04), ('Head', 42, 146, -0.06),
]
# limbs by two-bone IK: (upper, lower, end bone, end target, middle-joint hint, end-bone tip target)
LIMBS = [
    ('RightArm', 'RightForeArm', 'RightHand', (336, 140, -0.1), (290, 28, -0.06), (352, 186, -0.12)),
    ('LeftArm', 'LeftForeArm', 'LeftHand', (182, 226, -0.2), (132, 228, -0.12), (236, 242, -0.22)),
    ('RightUpLeg', 'RightLeg', 'RightFoot', (330, 200, -0.18), (245, 100, -0.14), (392, 206, -0.2)),
    ('LeftUpLeg', 'LeftLeg', 'LeftFoot', (466, 206, 0.05), (392, 150, 0.05), (492, 150, 0.0)),
]
HIPS_AT = (360, 150)


def sprite_point(x, y, depth):
    return Vector(((x - 254) * PX, depth, (258 - y) * PX))


def pose_traced(arm):
    world = lambda name, end='head': arm.matrix_world @ getattr(arm.pose.bones[M + name], end)
    for bone, x, y, depth in TRACE:
        cp.pose(arm, [('aim', M + bone, sprite_point(x, y, depth) - world(bone), 1.0)])
    for upper, lower, end, target, hint, tip in LIMBS:
        a = (world(upper, 'tail') - world(upper)).length
        b = (world(end) - world(lower)).length
        start = world(upper)
        goal = sprite_point(*target)
        d = goal - start
        reach = min(d.length, (a + b) * 0.999)
        axis = d.normalized()
        x = (a * a - b * b + reach * reach) / (2 * reach)
        h = math.sqrt(max(a * a - x * x, 0.0))
        pole = sprite_point(*hint) - start
        side = (pole - axis * pole.dot(axis)).normalized()
        middle = start + axis * x + side * h
        cp.pose(arm, [('aim', M + upper, middle - start, 1.0)])
        cp.pose(arm, [('aim', M + lower, start + axis * reach - world(lower), 1.0, M + end)])
        cp.pose(arm, [('aim', M + end, sprite_point(*tip) - world(end), 1.0)])


# Sprite proportions: the native skeleton has a larger ribcage and skull than the Meshy body. The chest pieces are
# widened about the spine line (lateral, now vertical; and front-back), the arms move out with the ribcage, the
# skull and jaw grow about the top of the neck.
CHEST_SCALE = (1.25, 1.3)           # lateral, front-back
SKULL_SCALE = 1.2
CHEST = {M + 'Spine1', M + 'Spine2'}
LOD2_TRIS = 470
LIMB_THICKEN = 1.25                  # the sprite's long bones are stouter than the Meshy body's


def eye_mask(obj):
    """Vertices of loose pieces whose texels are the red eye swatch."""
    image = bpy.data.images.load(os.path.join(ml.TEX, 'skeleton_basecolor.png'))
    w, h = image.size
    px = np.empty(w * h * 4, np.float32); image.pixels.foreach_get(px); px = px.reshape(h, w, 4)
    label, count = ml.loose_labels(obj)
    uv = obj.data.uv_layers[0].data
    red = np.zeros(count); total = np.zeros(count)
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            u, v = uv[li].uv
            c = px[min(h - 1, int(v * h)) % h, min(w - 1, int(u * w)) % w]
            p = label[obj.data.loops[li].vertex_index]
            red[p] += c[0] > 1.8 * c[1] + 0.05; total[p] += 1
    eyes = red / np.maximum(total, 1) > 0.5
    print('EYES pieces', int(eyes.sum()))
    return eyes[label]


FACE = (0.0, -1.0, 0.1)          # world direction the skull's face looks (toward the camera, a little left/down)


def face_toward(arm, name, direction):
    """Twist a bone about its own axis so the face (rest -y of the armature) looks along the world direction."""
    from mathutils import Vector
    pb = arm.pose.bones[name]
    bone = arm.data.bones[name]
    world = arm.matrix_world.to_3x3() @ pb.matrix.to_3x3() @ bone.matrix_local.to_3x3().inverted()
    front = world @ Vector((0, -1, 0))
    axis = (arm.matrix_world @ pb.tail - arm.matrix_world @ pb.head).normalized()
    want = Vector(direction).normalized()
    f = (front - axis * front.dot(axis)).normalized(); w = (want - axis * want.dot(axis)).normalized()
    angle = math.degrees(math.atan2(axis.dot(f.cross(w)), f.dot(w)))
    cp.pose(arm, [('twist', name, angle)])
    print('FACE twist', round(angle, 1))


def proportions(obj, joints):
    strongest = np.array(cp.strongest_bone(obj))
    co = np.array([v.co[:] for v in obj.data.vertices])
    a = np.array(joints[M + 'Spine1'][0]); b = np.array(joints[M + 'Neck'][0])
    axis = (b - a) / np.linalg.norm(b - a)
    lateral = np.array(joints[M + 'LeftArm'][0]) - np.array(joints[M + 'RightArm'][0])
    lateral -= axis * (lateral @ axis); lateral /= np.linalg.norm(lateral)
    depth = np.cross(axis, lateral)

    def widen(p):
        d = p - a
        t = d @ axis; l = d @ lateral; f = d @ depth
        return a + axis * t[..., None] + lateral * (l * CHEST_SCALE[0])[..., None] + depth * (f * CHEST_SCALE[1])[..., None]
    chest = np.isin(strongest, list(CHEST))
    co[chest] = widen(co[chest])
    for side in ('Left', 'Right'):
        shoulder = np.array(joints[M + side + 'Arm'][0])
        delta = widen(shoulder[None])[0] - shoulder
        mask = np.array([n.startswith(M + side) and not n.startswith(M + side + 'UpLeg') and 'Leg' not in n
                         and 'Foot' not in n and 'Toe' not in n for n in strongest])
        co[mask] += delta
    head = np.array(joints[M + 'Head'][0])
    skull = np.isin(strongest, [M + 'Head', M + 'Jaw'])
    co[skull] = head + (co[skull] - head) * SKULL_SCALE
    obj.data.vertices.foreach_set('co', co.ravel()); obj.data.update()


def thicken_limbs(obj, factor):
    """Scale each long-bone piece (arms and legs) about its own principal axis, perpendicular to it."""
    strongest = np.array(cp.strongest_bone(obj))
    label, count = ml.loose_labels(obj)
    co = np.array([v.co[:] for v in obj.data.vertices])
    limbs = ('Arm', 'ForeArm', 'UpLeg', 'Leg')
    for p in range(count):
        mask = label == p
        names = strongest[mask]
        bone = max(set(names), key=list(names).count)
        if not any(bone == M + side + part for side in ('Left', 'Right') for part in limbs):
            continue
        c = co[mask]; centre = c.mean(0)
        _, _, vt = np.linalg.svd(c - centre, full_matrices=False)
        axis = vt[0]
        d = c - centre; along = (d @ axis)[:, None] * axis
        co[mask] = centre + along + (d - along) * factor
    obj.data.vertices.foreach_set('co', co.ravel()); obj.data.update()


def source_level(mesh_index):
    """A copy of the skeleton GLB whose node shows the source's own LOD mesh `mesh_index` (0..3), so every level
    is posed from the reduction the creature project made for it."""
    import json
    import struct
    raw = open(SOURCE, 'rb').read()
    size = struct.unpack_from('<I', raw, 12)[0]
    document = json.loads(raw[20:20 + size]); binary = raw[20 + size:]      # BIN chunk with its header
    node = next(n for n in document['nodes'] if 'mesh' in n)
    node['mesh'] = mesh_index
    encoded = json.dumps(document, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    path = os.path.join(ml.WORK, f'skeleton_source_lod{mesh_index}.glb')
    with open(path, 'wb') as out:
        out.write(struct.pack('<III', 0x46546c67, 2, 20 + len(encoded) + len(binary))
                  + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded + binary)
    return path


# LOD0 budget per bone group (rev 2): long bones whole (their source pieces are already lean), the skull and jaw,
# ribcage, pelvis, hands, feet and small bones (vertebrae, clavicles, kneecaps) each decimated to their own share;
# the separate teeth are dropped (sub-pixel at game distance; the jaw and skull keep their tooth rows).
GROUPS = ['long', 'skull', 'ribcage', 'pelvis', 'hand', 'foot', 'small', 'teeth']
LOD0_SHARE = {'skull': 640, 'ribcage': 470, 'pelvis': 150, 'hand': 190, 'foot': 110, 'small': 140}


def tag_groups(obj):
    strongest = [b.replace(M, '') for b in cp.strongest_bone(obj)]
    label, count = ml.loose_labels(obj)
    co = np.array([v.co[:] for v in obj.data.vertices])
    group = np.zeros(len(co), np.int32)
    for p in range(count):
        mask = label == p
        names = [strongest[i] for i in np.flatnonzero(mask)]
        bone = max(set(names), key=names.count)
        diag = np.linalg.norm(np.ptp(co[mask], 0))
        if bone in ('Head', 'Jaw'):
            g = 'teeth' if diag < 0.06 else 'skull'
        elif bone == 'Spine2':
            g = 'ribcage'
        elif bone == 'Hips':
            g = 'pelvis'
        elif 'Hand' in bone:
            g = 'hand'
        elif 'Foot' in bone or 'Toe' in bone:
            g = 'foot'
        elif diag > 0.2:
            g = 'long'
        else:
            g = 'small'
        group[mask] = GROUPS.index(g)
    attr = obj.data.attributes.new('grp', 'INT', 'POINT')
    attr.data.foreach_set('value', group)


def decimate_groups(obj, name):
    values = np.empty(len(obj.data.vertices), np.int32)
    obj.data.attributes['grp'].data.foreach_get('value', values)
    parts = []
    for g, group in enumerate(GROUPS):
        if group == 'teeth' or not (values == g).any():
            continue
        part = ml.duplicate(obj, f'{name}_{group}')
        ml.delete_verts(part, values != g)
        if group in LOD0_SHARE:
            part = ml.decimate_pieces(part, LOD0_SHARE[group], 6 if group in ('hand', 'foot', 'small') else 10)
        parts.append(part)
    out = pl.join(name, parts)
    out.data.attributes.remove(out.data.attributes['grp'])
    return out


def posed(mesh_index, name):
    for o in list(bpy.data.objects):
        if o.type == 'ARMATURE' or (o.parent and o.parent.type == 'ARMATURE'):
            bpy.data.objects.remove(o)
    arm, body = cp.load(source_level(mesh_index))
    cp.place(arm, SIDE, sprite_point(*HIPS_AT, 0.0))
    cp.pose(arm, POSE)
    pose_traced(arm)
    face_toward(arm, M + 'Head', FACE)
    joints = {pb.name: (arm.matrix_world @ pb.head, arm.matrix_world @ pb.tail) for pb in arm.pose.bones}
    static = cp.bake(arm, body, name)
    proportions(static, joints)
    thicken_limbs(static, LIMB_THICKEN)
    tag_groups(static)
    for o in (arm, body):
        bpy.data.objects.remove(o)
    static.vertex_groups.clear()
    if 'rest' in static.data.attributes:
        static.data.attributes.remove(static.data.attributes['rest'])
    ml.delete_verts(static, eye_mask(static))
    return static


def main():
    preview = '--preview' in sys.argv
    pl.reset()
    mat = ml.material('Bone', 'skeleton', extras={'openyamm_specular': 0.35})
    static = posed(0, 'Skeleton')
    lo, hi = pl.bounds([static])
    offset = Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
    print('POSED tris', pl.triangles(static), 'size', [round(v, 3) for v in hi - lo])
    if preview:
        static.location = offset
        static.data.materials.clear(); static.data.materials.append(mat)
        pl.setup_render((768, 512))
        out = os.path.join(ml.HERE, 'review', 'skeleton')
        for tag, view in (('front', (0, 28)), ('top', (0, 85)), ('side', (90, 10)), ('tq', (40, 30))):
            pl.render_views([static], out, 'pose_' + tag, views=(view,))
        return
    static.name = 'SkeletonFull'
    levels = [decimate_groups(static, 'Skeleton')]
    levels[0].name = 'Skeleton'
    levels.append(posed(2, 'Skeleton_LOD1'))             # the creature's LOD2 (1,061) and LOD3 (417)
    far = ml.decimate_pieces(ml.duplicate(levels[1], 'Skeleton_LOD2'), LOD2_TRIS, 6)
    far.name = 'Skeleton_LOD2'
    levels.append(far)
    for lod in levels:
        lod.data.transform(Matrix.Translation(offset))
        lod.data.materials.clear(); lod.data.materials.append(mat)
        ml.smooth(lod)
        ml.colour(lod, distance=0.18, strength=0.9, power=1.4)
    print('LODS', [pl.triangles(o) for o in levels])
    ml.export(levels, 'skeleton')


main()
