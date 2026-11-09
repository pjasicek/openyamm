"""Bone kit: single bones cut from the project's MM6 skeleton creature (assets_source/worlds/mm6/models/mm6_ske.glb,
read only; 78 rigid bone pieces plus a skull with separate teeth and jaw, every piece 100 % on one mixamorig joint),
for the bone pile, carcass and carrion props. The rest pose is baked static and welded, the red eye swatches dropped;
pieces are addressed by joint and size rank, e.g. ('LeftUpLeg', 0) is the femur. place() copies pieces into a new
object with the bone's long axis along +x and its centre at the origin; drop() lays an object onto what is already
there (ray casts straight down), so piles stack without floating or deep intersections.
Usage (list the pieces): blender --background --python bonekit.py -- --list"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl, cp = ml.pl, ml.cp
SOURCE = os.path.join(ml.REPO, 'assets_source', 'worlds', 'mm6', 'models', 'mm6_ske.glb')
M = 'mixamorig:'


class Kit:
    def __init__(self):
        arm, body = cp.load(SOURCE)
        self.obj = cp.bake(arm, body, 'Kit')
        bones = np.array(cp.strongest_bone(self.obj))
        for o in (arm, body):
            bpy.data.objects.remove(o)
        self.obj.vertex_groups.clear()
        if 'rest' in self.obj.data.attributes:
            self.obj.data.attributes.remove(self.obj.data.attributes['rest'])
        eyes = self._eyes()
        keep = ~eyes
        ml.delete_verts(self.obj, eyes)
        self.bones = bones[keep]
        self.label, count = ml.loose_labels(self.obj)
        co = np.array([v.co[:] for v in self.obj.data.vertices])
        self.co = co
        self.pieces = []
        for p in range(count):
            mask = self.label == p
            names = list(self.bones[mask])
            bone = max(set(names), key=names.count).replace(M, '')
            c = co[mask]
            self.pieces.append({'id': p, 'bone': bone, 'n': int(mask.sum()), 'centre': c.mean(0),
                                'extent': c.max(0) - c.min(0), 'diag': float(np.linalg.norm(c.max(0) - c.min(0)))})
        self.obj.hide_render = True
        self.obj.hide_set(True)

    def _eyes(self):
        image = bpy.data.images.load(os.path.join(ml.TEX, 'skeleton_basecolor.png'), check_existing=True)
        w, h = image.size
        px = np.empty(w * h * 4, np.float32); image.pixels.foreach_get(px); px = px.reshape(h, w, 4)
        label, count = ml.loose_labels(self.obj)
        uv = self.obj.data.uv_layers[0].data
        red = np.zeros(count); total = np.zeros(count)
        for poly in self.obj.data.polygons:
            for li in poly.loop_indices:
                u, v = uv[li].uv
                c = px[int(v * h) % h, int(u * w) % w]
                p = label[self.obj.data.loops[li].vertex_index]
                red[p] += c[0] > 1.8 * c[1] + 0.05; total[p] += 1
        return (red / np.maximum(total, 1) > 0.5)[label]

    def find(self, bone, rank=0):
        found = sorted([p for p in self.pieces if p['bone'] == bone], key=lambda p: -p['diag'])
        return found[rank]['id']

    def ids(self, bone):
        return [p['id'] for p in self.pieces if p['bone'] == bone]

    def place(self, ids, name, align=True):
        """New object with the given pieces, centred at the origin, the long axis along +x when align."""
        obj = ml.duplicate(self.obj, name)
        obj.hide_render = False; obj.hide_set(False)
        ml.delete_verts(obj, ~np.isin(self.label, ids))
        co = np.array([v.co[:] for v in obj.data.vertices])
        centre = co.mean(0)
        rot = np.eye(3)
        if align:
            _, _, vt = np.linalg.svd(co - centre, full_matrices=False)
            rot = vt if np.linalg.det(vt) > 0 else vt * np.array([[1], [1], [-1]])
        co = (co - centre) @ rot.T
        obj.data.vertices.foreach_set('co', co.ravel()); obj.data.update()
        return obj


def transform(obj, rotation_deg=(0, 0, 0), location=(0, 0, 0), scale=1.0):
    from mathutils import Euler
    m = Matrix.LocRotScale(Vector(location), Euler([math.radians(a) for a in rotation_deg], 'XYZ'),
                           Vector((scale, scale, scale)))
    obj.data.transform(m); obj.data.update()
    return obj


def drop(obj, support, clearance=0.0, sink=0.0):
    """Lower obj straight down onto the ground (z = 0) or the support objects, whichever its vertices meet first,
    then sink it by `sink` metres (pieces settle into each other a little)."""
    trees = [BVHTree.FromObject(s, bpy.context.evaluated_depsgraph_get()) for s in support]
    co = np.array([v.co[:] for v in obj.data.vertices])
    gap = co[:, 2].min()                                  # distance to the ground
    for p in co[np.argsort(co[:, 2])[:max(40, len(co) // 3)]]:
        for tree in trees:
            hit = tree.ray_cast(Vector(p), Vector((0, 0, -1)), 2.0)
            if hit[0] is not None:
                gap = min(gap, p[2] - hit[0].z)
    obj.data.transform(Matrix.Translation((0, 0, -gap + clearance - sink))); obj.data.update()
    return obj


if __name__ == '__main__' and '--list' in sys.argv:
    pl.reset()
    kit = Kit()
    for p in sorted(kit.pieces, key=lambda p: (p['bone'], -p['diag'])):
        if p['diag'] > 0.03:
            print('KIT', p['id'], p['bone'], p['n'], round(p['diag'], 3), np.round(p['extent'], 3))


def eye_mask(obj):
    """Vertices of loose pieces whose texels are the skeleton's red eye swatch."""
    image = bpy.data.images.load(os.path.join(ml.TEX, 'skeleton_basecolor.png'), check_existing=True)
    w, h = image.size
    px = np.empty(w * h * 4, np.float32); image.pixels.foreach_get(px); px = px.reshape(h, w, 4)
    label, count = ml.loose_labels(obj)
    uv = obj.data.uv_layers[0].data
    red = np.zeros(count); total = np.zeros(count)
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            u, v = uv[li].uv
            c = px[int(v * h) % h, int(u * w) % w]
            p = label[obj.data.loops[li].vertex_index]
            red[p] += c[0] > 1.8 * c[1] + 0.05; total[p] += 1
    return (red / np.maximum(total, 1) > 0.5)[label]


def face_toward(arm, name, direction):
    """Twist a bone about its own axis so the face (rest -y of the armature) looks along the world direction."""
    pb = arm.pose.bones[name]
    bone = arm.data.bones[name]
    world = arm.matrix_world.to_3x3() @ pb.matrix.to_3x3() @ bone.matrix_local.to_3x3().inverted()
    front = world @ Vector((0, -1, 0))
    axis = (arm.matrix_world @ pb.tail - arm.matrix_world @ pb.head).normalized()
    want = Vector(direction).normalized()
    f = (front - axis * front.dot(axis)).normalized(); w = (want - axis * want.dot(axis)).normalized()
    angle = math.degrees(math.atan2(axis.dot(f.cross(w)), f.dot(w)))
    cp.pose(arm, [('twist', name, angle)])


def pose_skeleton(rotation, hips_at, ops, face=None, name='Posed'):
    """The whole skeleton posed (corpse_pose operations), baked static and welded, eyes dropped.
    Returns (object, joints {bone: (head, tail)} in world space, strongest bone name per remaining vertex)."""
    arm, body = cp.load(SOURCE)
    cp.place(arm, rotation, hips_at)
    cp.pose(arm, ops)
    if face is not None:
        face_toward(arm, M + 'Head', face)
    joints = {pb.name.replace(M, ''): (arm.matrix_world @ pb.head, arm.matrix_world @ pb.tail)
              for pb in arm.pose.bones}
    static = cp.bake(arm, body, name)
    bones = np.array([b.replace(M, '') for b in cp.strongest_bone(static)])
    for o in (arm, body):
        bpy.data.objects.remove(o)
    static.vertex_groups.clear()
    if 'rest' in static.data.attributes:
        static.data.attributes.remove(static.data.attributes['rest'])
    eyes = eye_mask(static)
    ml.delete_verts(static, eyes)
    return static, joints, bones[~eyes]


def along(kit, ids, a, b, thick=1.3, name='B'):
    """Kit piece(s) along the segment a -> b (length fitted, thickened across)."""
    obj = kit.place(ids, name)
    co = np.array([v.co[:] for v in obj.data.vertices])
    length = np.ptp(co[:, 0])
    a, b = Vector(a), Vector(b)
    d = b - a
    obj.data.transform(Matrix.Diagonal((d.length / length, thick, thick, 1.0)))
    round_ends(obj)
    rotation = Vector((1, 0, 0)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    obj.data.transform(Matrix.Translation((a + b) / 2) @ rotation)
    obj.data.update()
    return obj


def round_ends(obj, cap=0.65, keep=2.0):
    """A loose long bone aligned along x: the cut-off joint caps of the creature's bones (flat, dark-textured
    facets) become rounded condyles in the shaft's colour. Cap faces (normal along x, near an end) take the texture
    coordinate of the shaft's middle; one Catmull-Clark level rounds the ends; collapse back to `keep` times the
    source triangles."""
    me = obj.data
    co = np.array([v.co[:] for v in me.vertices])
    half = np.abs(co[:, 0]).max()
    uv = me.uv_layers[0].data
    shaft = [li for p in me.polygons if abs(p.center.x) < 0.25 * half for li in p.loop_indices]
    if shaft:
        coords = np.array([uv[li].uv[:] for li in shaft])
        mid = coords[np.argmin(np.linalg.norm(coords - np.median(coords, 0), axis=1))]   # a real shaft texel
        for p in me.polygons:
            if abs(p.center.x) > 0.85 * half or (abs(p.normal.x) > 0.35 and abs(p.center.x) > cap * half):
                for li in p.loop_indices:
                    uv[li].uv = mid
    start = pl.triangles(obj)
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new('S', 'SUBSURF'); mod.levels = 1; mod.uv_smooth = 'PRESERVE_BOUNDARIES'
    bpy.ops.object.modifier_apply(modifier=mod.name)
    pl.decimate_to(obj, int(start * keep))
    return obj
