"""Rigid-bone posing of the Meshy skeleton (no armature): rest joints measured on the A-pose mesh
(skeleton_joints.json, metres), capsule bones with a radius each, per-vertex weights from the bones' normalised
capsule distances (soft only within a short blend at the joints), and forward kinematics that aims each bone at a
target direction (from target joint positions), keeping the mesh's own bone lengths.

Joints: hips (pelvis centre), chest (spine at the ribcage bottom), neck (spine top), skull (skull base, top of the
neck), head_top, shoulder_l/r, elbow_l/r, wrist_l/r, finger_l/r (hand tip), hip_l/r, knee_l/r, ankle_l/r, toe_l/r.
_l is the skeleton's own left (+x in the rest mesh, which faces -y)."""
import math

import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

# name: (head joint, tail joint, parent, radius as a fraction of the skeleton height)
BONES = {
    'pelvis': ('hips', 'chest', None, 0.085),
    'chest': ('chest', 'neck', 'pelvis', 0.10),
    'neck': ('neck', 'skull', 'chest', 0.025),
    'head': ('skull', 'head_top', 'neck', 0.075),
}
for s in ('l', 'r'):
    BONES.update({
        f'upperarm_{s}': (f'shoulder_{s}', f'elbow_{s}', 'chest', 0.022),
        f'forearm_{s}': (f'elbow_{s}', f'wrist_{s}', f'upperarm_{s}', 0.02),
        f'hand_{s}': (f'wrist_{s}', f'finger_{s}', f'forearm_{s}', 0.03),
        f'thigh_{s}': (f'hip_{s}', f'knee_{s}', 'pelvis', 0.03),
        f'shin_{s}': (f'knee_{s}', f'ankle_{s}', f'thigh_{s}', 0.026),
        f'foot_{s}': (f'ankle_{s}', f'toe_{s}', f'shin_{s}', 0.03),
    })
ORDER = list(BONES)


def segment_distance(points, a, b):
    ab = b - a
    t = np.clip(((points - a) @ ab) / max(ab @ ab, 1e-12), 0.0, 1.0)
    return np.linalg.norm(points - (a + t[:, None] * ab), axis=1)


def weights(points, joints, height, blend=0.35, overrides=None):
    """(vertex count, bone count) weights: the bone with the smallest capsule distance / radius wins; a vertex whose
    second-best bone is within `blend` (normalised) of the best shares linearly (soft joints). overrides(points) ->
    {bone: boolean mask} forces vertices onto a bone (for example the pelvis below the lumbar spine)."""
    j = {k: np.array(v, float) for k, v in joints.items()}
    distances = np.stack([segment_distance(points, j[h], j[t]) / (r * height)
                          for h, t, _, r in BONES.values()], axis=1)
    order = np.argsort(distances, axis=1)
    best, second = order[:, 0], order[:, 1]
    rows = np.arange(len(points))
    gap = distances[rows, second] - distances[rows, best]
    share = np.clip(0.5 - gap / (2 * blend), 0.0, 0.5)
    w = np.zeros_like(distances)
    w[rows, best] = 1 - share
    w[rows, second] += share
    if overrides:
        for bone, mask in overrides(points, j).items():
            w[mask] = 0.0
            w[mask, ORDER.index(bone)] = 1.0
    return w


def aim(rotation_now, rest_direction, target_direction, twist=0.0):
    """Rotation (Matrix 3x3) that takes the bone's current direction onto the target, then twists about it."""
    current = rotation_now @ Vector(rest_direction)
    delta = current.rotation_difference(Vector(target_direction)).to_matrix()
    if twist:
        delta = Matrix.Rotation(math.radians(twist), 3, Vector(target_direction).normalized()) @ delta
    return delta @ rotation_now


def pose(joints, targets, root=None, twists=None, rotations=None):
    """Forward kinematics. joints: rest joints; targets: {joint: position} (only directions are used, from each
    bone's head target to its tail target; a bone whose tail target is missing keeps its parent's rotation);
    root: target hips position (default targets['hips']); twists: {bone: degrees about its own axis};
    rotations: {bone: Euler degrees} applied in world space after aiming (fine adjustments).
    Returns {bone: 4x4 Matrix mapping rest positions to posed ones} and the posed joints."""
    twists = twists or {}
    rotations = rotations or {}
    rest = {k: Vector(v) for k, v in joints.items()}
    posed_joints = {}
    transforms, spin = {}, {}
    for bone in ORDER:
        head, tail, parent, _ = BONES[bone]
        if parent is None:
            start = Vector(root if root is not None else targets['hips'])
            rotation_now = Matrix.Identity(3)
        else:
            start = transforms[parent] @ rest[head]
            rotation_now = spin[parent]
        rest_direction = rest[tail] - rest[head]
        if head in targets and tail in targets:
            rotation = aim(rotation_now, rest_direction, Vector(targets[tail]) - Vector(targets[head]),
                           twists.get(bone, 0.0))
        else:
            rotation = rotation_now
        if bone in rotations:
            rotation = Euler([math.radians(a) for a in rotations[bone]], 'XYZ').to_matrix() @ rotation
        spin[bone] = rotation
        transforms[bone] = Matrix.Translation(start) @ rotation.to_4x4() @ Matrix.Translation(-rest[head])
        posed_joints[head] = start
        posed_joints[tail] = transforms[bone] @ rest[tail]
    return transforms, posed_joints


def skin(points, w, transforms):
    out = np.zeros_like(points)
    homogeneous = np.c_[points, np.ones(len(points))]
    for index, bone in enumerate(ORDER):
        mask = w[:, index] > 0
        if not mask.any():
            continue
        m = np.array(transforms[bone])
        out[mask] += w[mask, index:index + 1] * (homogeneous[mask] @ m.T)[:, :3]
    return out
