"""Hide the Monk's hands inside his sleeves while the arms are folded (native hvf: the hands are tucked into the
sleeves when standing and walking; folded in the open they poked out over the fabric, user review 2026-10-20).
The folded wrist positions are Standing's mean wrist positions in the chest (B_Spine2) frame. In every clip, per frame,
each hand bone is keyed to a uniform scale from the distance of its wrist to that folded position: MIN_SCALE within
NEAR, full size beyond FAR, smoothstep between. The hand collapses onto the wrist joint, inside the sleeve; as the
arms unfold at the start of an attack, cast, hit, fidget or death the hand grows back. Hands are rigid (100 % hand
bone), so nothing else moves. Args: -- <in blend> <out blend>"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out = a[0], a[1]
MIN_SCALE, NEAR, FAR = 0.03, 0.08, 0.22
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']


def use(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def wrist_in_chest(s):
    return rig.pose.bones['B_Spine2'].matrix.inverted() @ rig.pose.bones[f'B_{s}_Hand'].head


def sstep(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


st = bpy.data.actions['Standing']; use(st)
f0, f1 = (int(round(x)) for x in st.frame_range)
ref = {s: Vector() for s in 'LR'}
for f in range(f0, f1 + 1):
    scene.frame_set(f)
    for s in 'LR':
        ref[s] += wrist_in_chest(s) / (f1 - f0 + 1)
for act in [x for x in bpy.data.actions if x.use_fake_user]:
    use(act)
    g0, g1 = (int(round(x)) for x in act.frame_range)
    lo, hi = 1.0, 0.0
    for f in range(g0, g1 + 1):
        scene.frame_set(f)
        for s in 'LR':
            k = MIN_SCALE + (1 - MIN_SCALE) * sstep(((wrist_in_chest(s) - ref[s]).length - NEAR) / (FAR - NEAR))
            pb = rig.pose.bones[f'B_{s}_Hand']; pb.scale = (k, k, k); pb.keyframe_insert('scale', frame=f)
            lo, hi = min(lo, k), max(hi, k)
    print('HIDEHANDS', act.name, 'frames', g1 - g0 + 1, 'hand scale', round(lo, 2), '..', round(hi, 2))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
