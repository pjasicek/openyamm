"""Preview the local running and stabbing candidates on their source character."""
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
for name in ['Standing Melee Attack Downward', 'Standing Melee Attack Horizontal', 'Orc Walk', 'Mutant Walking', 'Running (5)']:
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
    # Source grip axis crosses the palm from pinky to index; measured in hand space.
    hand = next(b for b in character.data.bones if b.name.endswith('RightHand'))
    index = next(b for b in character.data.bones if b.name.endswith('RightHandIndex1'))
    pinky = next(b for b in character.data.bones if b.name.endswith('RightHandPinky1'))
    middle = next(b for b in character.data.bones if b.name.endswith('RightHandMiddle1'))
    inv = hand.matrix_local.inverted()
    axis = (inv.to_3x3() @ (index.head_local-pinky.head_local)).normalized()
    forward = (inv @ middle.head_local).normalized()
    normal = axis.cross(forward).normalized()
    k = 1 / (character.matrix_world @ hand.matrix_local).to_scale()[0]
    center = inv @ middle.head_local + forward * 0.025*k - normal*0.025*k
    side = forward; flat = axis.cross(side).normalized()
    mesh = bpy.data.meshes.new('ClubEnvelope'); bm = bmesh.new()
    for a0,a1,w in [(-0.14,0.20,0.035),(0.20,0.68,0.07),(0.68,1.08,0.12)]:
        verts = [bm.verts.new(center + axis*a*k + side*x*w*k + flat*y*w*k)
                 for a in (a0,a1) for x in (-1,1) for y in (-1,1)]
        for face in [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]:
            bm.faces.new([verts[i] for i in face])
    bm.to_mesh(mesh); bm.free()
    club = bpy.data.objects.new('ClubEnvelope',mesh);scene.collection.objects.link(club)
    mat=bpy.data.materials.new('Club');mat.diffuse_color=(0.3,0.06,0.025,1);mesh.materials.append(mat)
    out = p / 'review/source_motion/Mixamo' 
    out.mkdir(exist_ok=True)
    for view in ['front', 'left', 'three_quarter']:
        row = []
        for i in range(9):
            frame = f0 + (f1 - f0) * i / 8
            scene.frame_set(int(frame), subframe=frame-int(frame))
            club.matrix_world = character.matrix_world @ character.pose.bones[hand.name].matrix
            filename = common.render_views(str(out / (name + '_' + str(i))),
                (lo.z + hi.z)/2, height*1.75, views=(view,), resolution=(240,320))[0]
            row.append([filename, name + ' ' + view + ' ' + str(round(frame))])
        rows.append(row)
(out / 'frames.json').write_text(json.dumps(rows))
print('MIXAMO_PREVIEW complete')
