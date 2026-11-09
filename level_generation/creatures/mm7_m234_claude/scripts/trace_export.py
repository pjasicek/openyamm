"""G6 trace on the EXPORTED GLB, played like the viewer (48 fps half-frames): per clip and bone group, the largest
world-rotation change between consecutive half-frames (deg), and the largest change of the hand relative to the
forearm. The reference is the SOURCE clip sampled the same way (its own fast swings are authored: the attack's hand
turns 148 deg per 30 fps frame); a group is flagged when ours exceeds the source's right hand by > 10 deg.
Args: -- <glb> [<role>=<set glb>:<clip> ...]"""
import bpy, sys, math
args = sys.argv[sys.argv.index('--') + 1:]
glb, refs = args[0], dict(x.split('=', 1) for x in args[1:])
SRCMAX = {}
for role, spec in refs.items():
    sg, clip = spec.rsplit(':', 1)
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=sg)
    sa = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    act = {x.name.split('@')[-1].split('|')[-1]: x for x in bpy.data.actions}[clip]; sa.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        sa.animation_data.action_slot = act.slots[0]
    SG = {'arms': ['B_L_UpperArm', 'B_R_UpperArm', 'B_L_Forearm', 'B_R_Forearm'], 'hands': ['B_L_Hand', 'B_R_Hand']}
    f0, f1 = act.frame_range; prev = None; m = {g: 0.0 for g in SG}; t = f0
    while t <= f1 + 1e-6:
        bpy.context.scene.frame_set(int(t), subframe=t - int(t))
        q = {n: (sa.matrix_world @ sa.pose.bones[n].matrix).to_quaternion() for ns in SG.values() for n in ns}
        if prev is not None:
            for g, ns in SG.items():
                for n in ns:
                    d = math.degrees(prev[n].rotation_difference(q[n]).angle); m[g] = max(m[g], min(d, 360 - d))
        prev = q; t += bpy.context.scene.render.fps / 48          # 1/48 s in the import's frame units
    SRCMAX[role] = m
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
GROUPS = {'arms': ['B_L_UpperArm', 'B_R_UpperArm', 'B_L_Forearm', 'B_R_Forearm'], 'hands': ['B_L_Hand', 'B_R_Hand'],
          'twist': ['B_L_ForearmTwist', 'B_R_ForearmTwist', 'B_L_UpperArmTwist', 'B_R_UpperArmTwist'],
          'fingers': [b.name for b in arm.data.bones if 'Finger' in b.name], 'sword': ['Sword']}
sc = bpy.context.scene
bad = 0
for act in bpy.data.actions:
    arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    prev, worst, rel_prev, rel_worst = None, {g: (0, 0) for g in GROUPS}, None, (0, 0)
    t = f0
    while t <= f1 + 1e-6:
        sc.frame_set(int(t), subframe=t - int(t))
        cur = {n: (arm.matrix_world @ arm.pose.bones[n].matrix).to_quaternion() for g in GROUPS.values() for n in g if n in arm.pose.bones}
        rel = {s: (arm.pose.bones[f'B_{s}_Forearm'].matrix.inverted() @ arm.pose.bones[f'B_{s}_Hand'].matrix).to_quaternion() for s in 'LR'}
        if prev is not None:
            for g, ns in GROUPS.items():
                for n in ns:
                    if n in cur:
                        d = math.degrees(prev[n].rotation_difference(cur[n]).angle); d = min(d, 360 - d)
                        if d > worst[g][0]:
                            worst[g] = (d, round(t, 1))
            for s in 'LR':
                d = math.degrees(rel_prev[s].rotation_difference(rel[s]).angle); d = min(d, 360 - d)
                if d > rel_worst[0]:
                    rel_worst = (d, round(t, 1))
        prev, rel_prev = cur, rel
        t += bpy.context.scene.render.fps / 48                     # 1/48 s in the import's frame units (scene rate)
    ref = SRCMAX.get(act.name, {'arms': 15.0, 'hands': 15.0})
    # arms and the twist bones (which follow the arms) against the source arms; hands, fingers, sword against its hands
    lim = {'arms': ref['arms'], 'twist': ref['arms'], 'hands': ref['hands'], 'fingers': ref['hands'], 'sword': ref['hands']}
    flags = [g for g, (d, _) in worst.items() if d > lim[g] + 10]
    bad += len(flags)
    print(f"TRACE {act.name:9s} max deg per half-frame: " + ', '.join(f"{g} {d:.1f}@{f}" for g, (d, f) in worst.items()) +
          f" | hand rel. forearm {rel_worst[0]:.1f}@{rel_worst[1]} | source arms/hands {ref['arms']:.1f}/{ref['hands']:.1f}" + (f"  FLAG {flags}" if flags else ''))
print('TRACE flags', bad)
