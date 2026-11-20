from pathlib import Path
import bpy, math
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/"work/rig_v5t.blend"))
rig=bpy.data.objects["Rig"]
def segment_axis(j, child):
    b, c = rig.data.bones[j], rig.data.bones[child]
    return (b.matrix_local.to_3x3().inverted() @ (c.head_local - b.head_local)).normalized()


TWIST_AXES = {'B_Spine': segment_axis('B_Spine', 'B_Spine1'), 'B_Spine1': segment_axis('B_Spine1', 'B_Spine2'),
              'B_Spine2': segment_axis('B_Spine2', 'B_Neck'), 'B_Neck': segment_axis('B_Neck', 'B_Head')}


def split_twist(q, axis):
    """q = swing @ twist about the bone-local axis; returns (swing, twist angle)."""
    t = 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(axis), q.w)
    t = (t + math.pi) % (2 * math.pi) - math.pi
    return q @ Quaternion(axis, t).inverted(), t


def limit_spine_twist(pose):
    parts = {j: split_twist(pose[j][0], TWIST_AXES[j]) for j in TWIST_AXES}
    total = sum(parts[j][1] for j in SPINE)
    if abs(total) <= TWIST_FREE:
        return pose, total, total
    span = TWIST_MAX - TWIST_FREE
    limited = math.copysign(TWIST_FREE + span * math.tanh((abs(total) - TWIST_FREE) / span), total)
    k = limited / total
    for j in SPINE:
        swing, t = parts[j]; pose[j] = (swing @ Quaternion(TWIST_AXES[j], t * k), pose[j][1])
    swing, t = parts['B_Neck']; pose['B_Neck'] = (swing @ Quaternion(TWIST_AXES['B_Neck'], t + total - limited),
                                                  pose['B_Neck'][1])
    return pose, total, limited



for act in [a for a in bpy.data.actions if a.use_fake_user]:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 angles=[]
 for f in range(int(act.frame_range[1])+1):
  bpy.context.scene.frame_set(f)
  angles.append(math.degrees(sum(split_twist(rig.pose.bones[n].rotation_quaternion,TWIST_AXES[n])[1] for n in ("B_Spine","B_Spine1","B_Spine2"))))
 print("SPINE",act.name,min(angles),max(angles))
