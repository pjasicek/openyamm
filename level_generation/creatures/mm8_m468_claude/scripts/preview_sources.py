"""G1 claw attack, stalking gait and idle candidates on their original mannequin."""
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector
import json
import sys
sys.path.insert(0, str(Path(__file__).parent))
import common
p = Path(__file__).resolve().parents[1]
lib = p.parents[2] / 'anim_library/mixamo'
rows = []
for name in ['Zombie Attack (1)', 'Mutant Swiping', 'Mutant Walking', 'Mutant Breathing Idle', 'Standard Run']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(lib / 'characters/warrok_w_kurniawan.fbx'))
    character = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    objects_before = set(bpy.data.objects)
    actions_before = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=str(lib / (name + '.fbx')))
    new_objects = set(bpy.data.objects) - objects_before
    source = next(o for o in new_objects if o.type == 'ARMATURE')
    action = next(iter(set(bpy.data.actions) - actions_before))
    assert set(source.pose.bones.keys()) <= set(character.pose.bones.keys()), 'Source character bone mismatch'
    character.animation_data_create()
    character.animation_data.action = action
    if action.slots:
        character.animation_data.action_slot = action.slots[0]
    for obj in new_objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    scene = bpy.context.scene
    common.workbench_clay(scene)
    f0, f1 = action.frame_range
    scene.frame_set(int(f0))
    lo, hi = common.world_bounds(meshes)
    height = hi.z - lo.z
    assert height > 0.5
    out = p / 'review/source_motion/Mixamo' 
    out.mkdir(parents=True,exist_ok=True)
    for view in ['front', 'left', 'three_quarter']:
        row = []
        for i in range(9):
            frame = f0 + (f1 - f0) * i / 8
            scene.frame_set(int(frame), subframe=frame-int(frame))
            filename = common.render_views(str(out / (name + '_' + str(i))),
                (lo.z + hi.z)/2, height*1.75, views=(view,), resolution=(240,320))[0]
            row.append([filename, name + ' ' + view + ' ' + str(round(frame))])
        rows.append(row)
(out / 'frames.json').write_text(json.dumps(rows))
print('MIXAMO_PREVIEW complete')
