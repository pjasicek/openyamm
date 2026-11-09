"""Walk smoothness probe (batch A/J walk review: head zigzag, ankle twitch): over the Walking loop at its 30 fps keys,
the head joint's world height (range and largest |second difference|, cm), the pelvis height range (cm), and per
foot the largest change of the world-rotation step between consecutive frames (deg; a foot that twitches as it lands
shows a large value). Args: -- <blend> [action]"""
import bpy, sys, math
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
an = a[1] if len(a) > 1 else 'Walking'
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
hz, pz, fq = [], [], {s: [] for s in 'LR'}
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    W = lambda b: rig.matrix_world @ rig.pose.bones[b].matrix
    hz.append(W('B_Head').translation.z); pz.append(W('B_Pelvis').translation.z)
    for s in 'LR':
        fq[s].append(W(f'B_{s}_Foot').to_quaternion())
hz, pz = np.array(hz), np.array(pz)
d2 = np.abs(hz[2:] - 2 * hz[1:-1] + hz[:-2])
out = {}
for s in 'LR':
    st = [math.degrees(min(x, 2 * math.pi - x)) for x in (fq[s][i].rotation_difference(fq[s][i + 1]).angle for i in range(len(fq[s]) - 1))]
    out[s] = round(max(abs(st[i + 1] - st[i]) for i in range(len(st) - 1)), 1)
print(f'WALKPROBE {an}: head z {100 * hz.min():.1f}..{100 * hz.max():.1f} cm, max |d2| {100 * d2.max():.2f} cm; '
      f'pelvis range {100 * (pz.max() - pz.min()):.1f} cm; foot rotation step change max deg {out}')
