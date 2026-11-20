"""Source clip pronation: twist of the hand against the upper arm about the forearm direction (Mixamo slash)."""
import bpy, math
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(P.parents[2] / 'anim_library/mixamo/Great Sword Slash (2).fbx'))
src = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); sc = bpy.context.scene
pre = next(b.name for b in src.pose.bones if b.name.endswith('Hips'))[:-4]
a = src.animation_data.action; f0, f1 = a.frame_range
def W(n): return src.matrix_world @ src.pose.bones[pre + n].matrix
def tw(q, axis):
    t = 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(axis), q.w); return math.degrees((t + math.pi) % (2 * math.pi) - math.pi)
rest = {}
for side in ('Right', 'Left'):
    out_f, out_h = [], []
    for k in range(int((f1 - f0) * 2) + 1):
        sc.frame_set(int(f0 + k / 2), subframe=(k / 2) % 1)
        u, f, h = W(side + 'Arm'), W(side + 'ForeArm'), W(side + 'Hand')
        ax = (h.translation - f.translation).normalized()
        # forearm roll vs upper arm and hand twist vs forearm, about the forearm direction (world)
        qf = (f.to_quaternion() @ u.to_quaternion().inverted()); qh = (h.to_quaternion() @ f.to_quaternion().inverted())
        out_f.append(round(tw(qf, ax), 1)); out_h.append(round(tw(qh, ax), 1))
    print('SRC', side, 'forearm-vs-upper', out_f)
    print('SRC', side, 'hand-vs-forearm', out_h)
