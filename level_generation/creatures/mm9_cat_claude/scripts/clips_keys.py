"""Authored role clips for MM9 animals whose ABC has no such clip (Hit, Death, the cat's swipe). A clip is a list of key
poses: a base pose from an MM9 clip plus rotations and offsets given in armature space (the animal faces -Y, +Z up), so
the keys read the same whatever the bones' rest frames are. The keys go through the same monotone cubic resampling as the
MM9 clips (clips_mm9.write_action), so holds stay holds and nothing overshoots.

keyed(arm, base, keys) -> (rec, duration)
  base: {bone: (q, l, s)}; keys: [(time, [(bone, 'rot', (ax, ay, az), degrees) | (bone, 'loc', (x, y, z)), ...]), ...]
Deltas of one key are applied in the given order, parents first."""
import bpy
from mathutils import Matrix, Quaternion, Vector


def pose_of(rec_by_bone, t):
    """Pose of an MM9 record at time t (nearest keys, linear): {bone: (q, l, s)}."""
    out = {}
    for b, r in rec_by_bone.items():
        ts = r['t']
        if t <= ts[0]:
            i, a = 0, 0.0
        elif t >= ts[-1]:
            i, a = len(ts) - 2, 1.0
        else:
            i = max(k for k in range(len(ts) - 1) if ts[k] <= t)
            a = (t - ts[i]) / max(ts[i + 1] - ts[i], 1e-9)
        q = r['q'][i].slerp(r['q'][i + 1], a) if len(ts) > 1 else r['q'][0]
        l = r['l'][i].lerp(r['l'][i + 1], a) if len(ts) > 1 else r['l'][0]
        s_ = r['s'][i].lerp(r['s'][i + 1], a) if len(ts) > 1 else r['s'][0]
        out[b] = (q.copy(), l.copy(), s_.copy())
    return out


def keyed(arm, base, keys):
    vl = bpy.context.view_layer
    if arm.animation_data:
        arm.animation_data.action = None
    rec = {b: {'t': [], 'q': [], 'l': [], 's': []} for b in base}
    for t, deltas in keys:
        for pb in arm.pose.bones:
            pb.rotation_mode = 'QUATERNION'
            if pb.name in base:
                pb.rotation_quaternion, pb.location, pb.scale = base[pb.name]
            else:
                pb.matrix_basis.identity()
        vl.update()
        for d in deltas:
            pb = arm.pose.bones[d[0]]
            h = pb.head.copy()
            if d[1] == 'rot':
                R = Quaternion(Vector(d[2]).normalized(), __import__('math').radians(d[3])).to_matrix().to_4x4()
                pb.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ pb.matrix
            else:
                pb.matrix = Matrix.Translation(Vector(d[2])) @ pb.matrix
            vl.update()
        for b, r in rec.items():
            pb = arm.pose.bones[b]
            r['t'].append(t); r['q'].append(pb.rotation_quaternion.copy())
            r['l'].append(pb.location.copy()); r['s'].append(pb.scale.copy())
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    vl.update()
    return rec, keys[-1][0]
