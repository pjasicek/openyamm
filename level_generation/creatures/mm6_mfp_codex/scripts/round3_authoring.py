"""Synchronize the editable Death timeline without changing poses or any other data."""
import bpy
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
W = P / 'work/round3'
def remap(frame, fps):
    t = frame / fps
    return (min(t, 100 / 48) + max(t - 100 / 48, 0) / 1.5) / 1.25 * fps
def curves(action):
    return [fc for layer in action.layers for strip in layer.strips
            for bag in strip.channelbags for fc in bag.fcurves]

receipts = []
paths = [(P / 'work/round2' / f'lod{i}.blend', W / f'lod{i}.blend') for i in range(4)]
paths.append((W / 'before/export/mm6_mfp.blend', P / 'export/mm6_mfp.blend'))
for src, dst in paths:
    bpy.ops.wm.open_mainfile(filepath=str(src))
    bpy.context.preferences.filepaths.save_version = 0
    fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    action = bpy.data.actions['Death']
    old_range = list(action.frame_range)
    changed = 0
    for fc in curves(action):
        assert all(k.interpolation in ('LINEAR', 'CONSTANT') for k in fc.keyframe_points)
        if any(abs(k.co.x - 100 / 48 * fps) < 1e-4 for k in fc.keyframe_points):
            pass
        else:
            # Add the exact speed-change boundary without changing linear source motion.
            x = 100 / 48 * fps
            key = fc.keyframe_points.insert(x, fc.evaluate(x))
            key.interpolation = 'LINEAR'
        for k in fc.keyframe_points:
            y, left_y, right_y = k.co.y, k.handle_left.y, k.handle_right.y
            k.co.x = remap(k.co.x, fps)
            k.handle_left.x = remap(k.handle_left.x, fps)
            k.handle_right.x = remap(k.handle_right.x, fps)
            assert (k.co.y, k.handle_left.y, k.handle_right.y) == (y, left_y, right_y)
            changed += 1
        fc.update()
    if action.use_frame_range:
        action.frame_start = remap(action.frame_start, fps)
        action.frame_end = remap(action.frame_end, fps)
    bpy.ops.wm.save_as_mainfile(filepath=str(dst))
    receipts.append({'source': str(src.relative_to(P)), 'output': str(dst.relative_to(P)),
                     'fps': fps, 'old_frame_range': old_range,
                     'new_frame_range': list(action.frame_range), 'death_keys_retimed': changed})
(P / 'review/round3/authoring.json').write_text(json.dumps(receipts, indent=2) + '\n')
print('ROUND3_AUTHORING', receipts, flush=True)
