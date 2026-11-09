"""Stride of a grounded in-place cycle: the planted toe's backward sweep D over its stance time, scaled to the cycle
(stride = D x cycle / stance time). Writes work/strides.json. Args: -- <clip> [<clip> ...] (on work/assembly_all.blend)"""
import bpy, sys, os, json
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work', 'assembly_all.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; out = {}
for clip in sys.argv[sys.argv.index('--') + 1:]:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if act.slots: rig.animation_data.action_slot = act.slots[0]
    n = int(act.frame_range[1]); res = []
    for side in 'LR':
        T = []
        for f in range(n + 1):
            sc.frame_set(f); T.append(rig.pose.bones[f'B_{side}_Toe0'].head.copy())
        zmin = min(p.z for p in T); st = [i for i, p in enumerate(T) if p.z < zmin + 0.015]
        if len(st) < 2: continue
        D = abs(T[st[-1]].y - T[st[0]].y); res.append(D * n / max(st[-1] - st[0], 1))
    out[clip] = round(sum(res) / len(res), 3)
    print('STRIDE', clip, out[clip], flush=True)
json.dump(out, open(os.path.join(P, 'work', 'strides.json'), 'w'), indent=1)
sys.stdout.flush(); os._exit(0)
