"""Source-animation scan for faults the user notices in the viewer: blender -b -P clip_scan.py -- <glb>. Samples every
clip at 48 fps (viewer frame = time x 48) and prints, per clip: per-frame jumps of tracked bone heads in model space
(Root, Chest, Head, both hands, rollers; a step over 3x the clip's median step and over 1.5 cm), the motion-start time
(first frame where any tracked point has moved 1 cm from frame 0; dead starts in Attack), and the loop seam step."""
import sys, bpy, numpy as np
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); sc = bpy.context.scene
fps = sc.render.fps / sc.render.fps_base
track = [b for b in ('Root', 'Waist', 'Chest', 'Head', 'Hand_L', 'Hand_R', 'Roller_0', 'Roller_1', 'Roller_2') if b in rig.pose.bones]
for act in bpy.data.actions:
    rig.animation_data.action = act
    if act.slots: rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; dur = (f1 - f0) / fps; n = int(round(dur * 48)) + 1
    pos = []
    for k in range(n):
        f = f0 + k / 48 * fps; sc.frame_set(int(f), subframe=f - int(f))
        pos.append([(rig.matrix_world @ rig.pose.bones[b].head)[:] for b in track])
    pos = np.array(pos)  # frames x bones x 3
    if n < 3:
        print(f'CLIP {act.name} {dur:.3f}s held pose'); continue
    step = np.linalg.norm(np.diff(pos, axis=0), axis=2)  # (n-1) x bones
    med = np.median(step, axis=0) + 1e-6
    jumps = [(k + 1, track[j], step[k, j]) for k in range(len(step)) for j in range(len(track)) if step[k, j] > max(3 * med[j], .015)]
    moved = np.linalg.norm(pos - pos[0], axis=2).max(1); start = next((k for k in range(n) if moved[k] > .01), None)
    seam = np.linalg.norm(pos[-1] - pos[0], axis=1).max()
    zc = pos[:, track.index('Head'), 2]
    print(f'CLIP {act.name} {dur:.3f}s frames 0-{n - 1}: motion starts frame {start} ({start / 48 if start is not None else 0:.3f}s); '
          f'loop seam {seam * 1000:.1f} mm; head z {zc.min():.3f}-{zc.max():.3f}; max step per bone (mm) ' +
          ', '.join(f'{b} {step[:, j].max() * 1000:.0f}' for j, b in enumerate(track)))
    for k, b, s in jumps[:12]:
        print(f'   JUMP {act.name} frame {k - 1}->{k} {b} {s * 1000:.1f} mm (median {med[track.index(b)] * 1000:.1f})')
