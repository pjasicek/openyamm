"""Neck bend spread on the delivered dog clips (Blender module used by build_export.py).

MM9's clips put up to 83 degrees between neck and head in one joint (Xheadpiv); the low-poly MM9 mesh hides it, our denser
skin folds the nape into a spike. Part of that joint's turn moves up the neck: Xheadpiv keeps KEEP_HEAD of its delta, the rest
goes to XneckA and XneckB (SHARE_B of it on XneckB). The product of the three joints is unchanged, so the head keeps MM9's
world orientation exactly and only its position moves a little along the curved neck. Keys of the three bones are rewritten
on every frame; loop ends stay equal."""
import bpy
from mathutils import Quaternion

KEEP_HEAD = 0.4
SHARE_B = 0.45


def rest_local(rig, name):
    b = rig.data.bones[name]
    return (b.parent.matrix_local.inverted() @ b.matrix_local).to_quaternion()


def power(q, t):
    return Quaternion().slerp(q, t)


def spread(rig, actions):
    sc = bpy.context.scene
    B, A, H = (rig.pose.bones[n] for n in ('XneckB', 'XneckA', 'Xheadpiv'))
    r0a, r0h = rest_local(rig, 'XneckA'), rest_local(rig, 'Xheadpiv')
    for act in actions:
        rig.animation_data.action = act
        f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        out = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            d = H.rotation_quaternion.normalized()
            a = A.rotation_quaternion.normalized()
            b = B.rotation_quaternion.normalized()
            h2 = power(d, KEEP_HEAD)
            x = r0h @ power(d, 1 - KEEP_HEAD) @ r0h.inverted()     # moved out of Xheadpiv, in XneckA's frame
            la = r0a @ a
            y = power(la @ x @ la.inverted(), SHARE_B)             # the part XneckB takes over, in XneckB's frame
            out.append((f, b @ y, a @ power(x, 1 - SHARE_B), h2))
        for f, qb, qa, qh in out:
            for pb, q in ((B, qb), (A, qa), (H, qh)):
                pb.rotation_quaternion = q
                pb.keyframe_insert('rotation_quaternion', frame=f)
    return {'keep_head': KEEP_HEAD, 'share_b': SHARE_B}
