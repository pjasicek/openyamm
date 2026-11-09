"""m262: the one-shot clips ease from and to the FLIGHT pose (Walking frame 0, after the knife carry and the twist
rebake), not to Standing frame 0: the harpy never stands, every action starts and ends in the flight loop, and the
upright idle's hanging arms pass through her feathered thighs (G6: 5-6 cm at the clips' ends). Every bone except the
legs, the tail and the wings (hover.py keys them; wings_anim.py comes later) is slerped from the flight pose to the
clip over BLEND_IN s and back over BLEND_OUT s (smoothstep). Args: -- <in blend> <out blend>"""
import bpy, sys, os
src, out = sys.argv[sys.argv.index('--') + 1:]
FPS = 30
SPEC = {'Attack': (0.30, 0.30), 'Hit': (0.15, 0.20), 'Death': (0.25, 0.0)}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']
SKIP = lambda n: any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe', 'B_Tail', 'Wing_'))


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def ss(t):
    t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)


set_act(bpy.data.actions['Walking']); scene.frame_set(0)
fly = {pb.name: pb.matrix_basis.to_quaternion() for pb in rig.pose.bones}
for name, (tin, tout) in SPEC.items():
    act = bpy.data.actions[name]; set_act(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); T = (f1 - f0) / FPS
    for f in range(f0, f1 + 1):
        scene.frame_set(f); t = (f - f0) / FPS
        w = ss(t / tin) if tin > 0 else 1.0
        if tout > 0:
            w = min(w, ss((T - t) / tout))
        for pb in rig.pose.bones:
            if SKIP(pb.name):
                continue
            q = pb.matrix_basis.to_quaternion(); qf = fly[pb.name]
            if q.dot(qf) < 0:
                qf = -qf
            pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = qf.slerp(q, w)
            pb.keyframe_insert('rotation_quaternion', frame=f)
    set_act(None)
    print('FLIGHTBLEND', name, 'frames', f1 - f0 + 1, 'in', tin, 'out', tout)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
