"""Rig-only GLB of the master_motion.blend clips with export.py's settings (192 Hz key scale, NLA tracks), for
transplanting re-authored clips into an existing runtime GLB (Standing v2). Walk is left out: export.py and
build_runtime.py retime it. Usage: blender -b -P export_clips.py -- <out.glb> [blend, default master_motion.blend]"""
import bpy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]; out = args[0]
bpy.ops.wm.open_mainfile(filepath=args[1] if len(args) > 1 else str(P / 'master_motion.blend'))
rig = bpy.data.objects['Lizardman_Rig']; sc = bpy.context.scene
rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.matrix_basis.identity()
for track in list(rig.animation_data.nla_tracks):
    if track.name == 'Walk':
        rig.animation_data.nla_tracks.remove(track)
for name in ['Standing', 'Hit', 'Fidget', 'Death', 'Corpse']:
    action = bpy.data.actions[name]; factor = 4; end = float(action.frame_range[1]) * factor
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:
                        key.co.x *= factor; key.handle_left.x *= factor; key.handle_right.x *= factor
                    fc.update()
    strip = next(t for t in rig.animation_data.nla_tracks if t.name == name).strips[0]
    strip.action_frame_end = end; strip.frame_end = end
sc.render.fps = 192
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True,
    export_animation_mode='NLA_TRACKS', export_frame_range=False, export_force_sampling=False, export_yup=True,
    export_extras=True, export_attributes=False)
