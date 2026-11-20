"""Compare owned cast clips on their source rig with a short-wand stand-in."""
from pathlib import Path
import hashlib
import json
import math
import runpy
import sys

import bpy
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
sys.path.insert(0, str(P.parent / 'mm6_natm_claude/scripts'))
import common

out = P / 'review/source_casts'
out.mkdir(parents=True, exist_ok=True)
(P / 'work').mkdir(exist_ok=True)
grip_script = P / 'scripts/grip_from_source.py'
sys.argv = [str(grip_script), '--', str(ROOT / 'anim_library/humanoid_set/Armed.glb'), 'ArmedCastRAttack1:0']
runpy.run_path(str(grip_script), run_name='__main__')
grip = json.loads((P / 'work/grip_source.json').read_text())
records = []
for library, clips in [('Armed', ['ArmedCastRAttack1', 'ArmedCastRAttack2', 'ArmedCastRAttack3']),
                       ('Unarmed', ['UnarmedCastDualAttack2'])]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    source = ROOT / f'anim_library/humanoid_set/{library}.glb'
    bpy.ops.import_scene.gltf(filepath=str(source))
    rig = next(o for o in scene.objects if o.type == 'ARMATURE')
    rig.rotation_mode = 'XYZ'
    rig.rotation_euler.z = math.pi
    bpy.context.view_layer.update()
    for obj in list(scene.objects):
        if obj.type == 'MESH' and obj.parent != rig:
            obj.hide_render = True
    common.workbench_clay(scene)
    wand = []
    if library == 'Armed':
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=.023, depth=.45)
        wand.append(bpy.context.object)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=.08)
        wand.append(bpy.context.object)
        for obj in wand:
            obj.color = (.12, .32, .8, 1)
    acts = list(bpy.data.actions)
    for name in clips:
        act = next(a for a in acts if a.name.endswith(name))
        rig.animation_data.action = act
        if getattr(act, 'slots', None):
            rig.animation_data.action_slot = act.slots[0]
        f0, f1 = act.frame_range
        assert abs((f1 - f0) / 30 - 1.) < .001, (name, f0, f1)
        rows, motion = [], []
        for index in range(31):
            frame = f0 + index
            scene.frame_set(int(frame), subframe=frame % 1)
            hand = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
            centre = hand @ Vector(grip['centre_hand'])
            axis = (hand.to_3x3() @ Vector(grip['axis_hand'])).normalized()
            if wand:
                wand[0].location = centre + axis * .12
                wand[0].rotation_mode = 'QUATERNION'
                wand[0].rotation_quaternion = Vector((0, 0, 1)).rotation_difference(axis)
                wand[1].location = centre + axis * .345
            motion.append({'t': index / 30, 'wand_tip':list(centre + axis * .425),
                           'joints':{n:list((rig.matrix_world @ b.matrix).translation)
                                     for n,b in rig.pose.bones.items() if n.startswith('B_')}})
            paths = common.render_views(str(out / f'{name}_{index:02d}'), 1.25, 2.9,
                                         views=('front','left','three_quarter'), resolution=(400,360))
            rows.append(paths)
        assert len(motion) == 31 and all(math.isfinite(x) for k in motion for x in k['wand_tip'])
        records.append({'clip':name, 'source':str(source.relative_to(ROOT)),
                        'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                        'fps':30,'duration_seconds':(f1-f0)/30,'frames':rows,'motion':motion,
                        'prop': 'short wand stand-in, grip derived from source' if wand else 'none (Djinn comparison)'})
(out/'clips.json').write_text(json.dumps(records,indent=2)+'\n')
print('CAST_PREVIEWS', [(r['clip'],r['duration_seconds'],len(r['frames'])) for r in records])
