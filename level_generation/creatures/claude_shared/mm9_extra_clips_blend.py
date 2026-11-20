"""Dropped MM9 clips on a Blender-route MM9 body (run2-clips-groupC, 2026-10-31): Blender module, imported by a
project's own `scripts/extra_clips_blend.py` shim (tools/run_creature_blender.sh only runs scripts inside a project).

The shim names the project's MM9 source blend (the file its build_export.py opens, holding the imported MM9 actions)
and a role table {role: ([source clips], loop)}. The roles are built with the project's OWN clips_mm9.py functions
(read_keys, close_seam, stitch, write_action: the same PCHIP resample, seam closing and stitch blends as the accepted
clips; build_role_clips(arm, fps, roles) itself when the project's copy takes a role table), then only the armature
and those actions are exported with build_export.py's glTF settings. graft_clips.py then grafts them onto the
installed export, whose rest pose must match.

Shim usage: <blender> --python scripts/extra_clips_blend.py -- <source blend> <out glb> <report json>
"""
import importlib
import inspect
import json
import os
import sys

import bpy


def build(C, rig, fps_import, roles):
    if 'roles' in inspect.signature(C.build_role_clips).parameters:
        report = C.build_role_clips(rig, fps_import, roles)
        return report, report.pop('_recs', {})
    sources, durations = {}, {}
    for act in list(bpy.data.actions):
        sources[act.name] = C.read_keys(act, fps_import)
        any_bone = next(iter(sources[act.name].values()))
        durations[act.name] = any_bone['t'][-1] - any_bone['t'][0]
    report = {'fps': C.FPS, 'clips': {}}
    recs = {}
    for role, (names, loop) in roles.items():
        if len(names) == 1:
            rec = {b: {k: list(v) for k, v in r.items()} for b, r in sources[names[0]].items()}
            if loop:
                for r in rec.values():
                    C.close_seam(r)
            duration = durations[names[0]]
            info = {'sources': names, 'loop': loop}
        else:
            rec, jumps = C.stitch([sources[n] for n in names], [durations[n] for n in names])
            duration = sum(durations[n] for n in names)
            info = {'sources': names, 'loop': False,
                    'join_jump_deg': [round(max(j[i] for j in jumps.values()), 2) for i in range(len(names) - 1)]}
        act, n = C.write_action(rig, role, rec, duration, loop)
        info['duration'] = n / C.FPS
        info['frames'] = n
        report['clips'][role] = info
        recs[role] = rec
    return report, recs


def hold_evaluated(rig, name, role, C):
    """build_export.py's Dead: the pose bones evaluated at the role action's last frame, held one second."""
    sc = bpy.context.scene
    act = bpy.data.actions[role] if role in bpy.data.actions else next(
        a for a in bpy.data.actions if a.name.rsplit('.', 1)[0] == role)
    rig.animation_data.action = act
    sc.frame_set(int(round(act.frame_range[1])))
    end = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
    dead = bpy.data.actions.new(name)
    dead.use_fake_user = True
    rig.animation_data.action = dead
    for f in (0, C.FPS):
        for pb in rig.pose.bones:
            q, l, s_ = end[pb.name]
            pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion, pb.location, pb.scale = q, l, s_
            pb.keyframe_insert('rotation_quaternion', frame=f)
            pb.keyframe_insert('location', frame=f)
            pb.keyframe_insert('scale', frame=f)


def main(scripts_dir, roles, rig_name=None, prep=None, post=None, clips_module='clips_mm9', holds=None, hold_mode='rec',
         pre_export=None, post_first=False):
    """holds: {name: role}, the role's last pose held one second (C.hold_action), e.g. a temporary Dead2 for
    floor_fix --ground-death Death2 Dead2."""
    argv = sys.argv[sys.argv.index('--') + 1:]
    in_blend, out_glb, report_path = argv[:3]
    sys.path.insert(0, scripts_dir)
    C = importlib.import_module(clips_module)
    bpy.ops.wm.open_mainfile(filepath=in_blend)
    sc = bpy.context.scene
    rig = bpy.data.objects[rig_name] if rig_name else next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    if prep:
        prep(rig)
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
    bpy.context.view_layer.update()
    fps_import = sc.render.fps / sc.render.fps_base
    originals = list(bpy.data.actions)
    names = sorted({n for names, _ in roles.values() for n in names})
    missing = [n for n in names if n not in {a.name for a in originals}]
    if missing:
        raise SystemExit(f'source blend lacks MM9 clips {missing}; has {[a.name for a in originals]}')
    report, recs = build(C, rig, fps_import, roles)
    if post and post_first:
        post(rig, report, C)
    for name, role in (holds or {}).items():
        if hold_mode == 'eval':
            hold_evaluated(rig, name, role, C)
        else:
            C.hold_action(rig, name, recs[role])
        report['clips'][name] = {'sources': [role + ' last pose'], 'duration': 1.0}
    if post and not post_first:
        post(rig, report, C)
    for a in originals:
        bpy.data.actions.remove(a)
    keep = set(roles) | set(holds or {})
    for a in list(bpy.data.actions):
        # a role named like its source clip (Glide) was created as Glide.001 while the source existed
        base = a.name.rsplit('.', 1)[0]
        if a.name not in keep and base in keep and base not in {b.name for b in bpy.data.actions}:
            a.name = base
    for a in list(bpy.data.actions):
        if a.name not in roles and a.name not in (holds or {}):
            bpy.data.actions.remove(a)
    sc.render.fps = C.FPS
    sc.render.fps_base = 1
    rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
    if pre_export:
        pre_export(rig)
    for o in bpy.data.objects:
        o.select_set(o == rig)
    bpy.context.view_layer.objects.active = rig
    os.makedirs(os.path.dirname(os.path.abspath(out_glb)), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out_glb, use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                              export_frame_step=1, export_skins=True, export_all_influences=False,
                              export_attributes=False, export_morph=False,
                              export_reset_pose_bones=True, export_anim_slide_to_zero=True)
    json.dump(report, open(report_path, 'w'), indent=1, default=str)
    print('EXTRA EXPORTED', out_glb, json.dumps({k: v.get('duration') for k, v in report['clips'].items()}))
