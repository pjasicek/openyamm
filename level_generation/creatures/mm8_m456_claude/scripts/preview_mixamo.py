"""G1: inspect existing Mixamo clips on their own Warrok mannequin, with a sword stand-in."""
from pathlib import Path
import bpy
import json
import math
import sys
from mathutils import Vector, Matrix

project = Path(__file__).resolve().parents[1]
repo = project.parents[2]
sys.path.insert(0, str(project / 'scripts'))
import common

library = repo / 'anim_library/mixamo'
clips = ['Standard Idle', 'Walk', 'Standard Run', 'Sword And Shield Slash', 'Stable Sword Inward Slash', 'Stable Sword Outward Slash',
         'Standing React Death Backward', 'Standing Taunt Battlecry']
rows = {view: [] for view in ['front', 'left', 'three_quarter']}
report = {}
for clip in clips:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    bpy.ops.import_scene.fbx(filepath=str(library / 'characters/warrok_w_kurniawan.fbx'))
    character = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(library / (clip + '.fbx')))
    source = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
    action = source.animation_data.action
    # Fit the library mannequin to each clip's bind skeleton before playing its untouched animation.
    errors = [(character.matrix_world @ character.data.bones[b.name].head_local -
               source.matrix_world @ b.head_local).length for b in source.data.bones
              if b.name in character.data.bones]
    assert errors and max(errors) < 0.1, (clip, max(errors))
    transforms = {b.name: source.matrix_world @ source.data.bones[b.name].matrix_local @
                  (character.matrix_world @ b.matrix_local).inverted()
                  for b in character.data.bones if b.name in source.data.bones}
    for mesh in [o for o in before if o.type == 'MESH']:
        world = mesh.matrix_world.copy()
        for vertex in mesh.data.vertices:
            weights = [(transforms[mesh.vertex_groups[g.group].name], g.weight)
                       for g in vertex.groups if mesh.vertex_groups[g.group].name in transforms]
            total = sum(w for _, w in weights)
            if total:
                point = world @ vertex.co
                vertex.co = world.inverted() @ sum((m @ point * w for m, w in weights), Vector()) / total
        for modifier in mesh.modifiers:
            if modifier.type == 'ARMATURE':
                modifier.object = source
        mesh.parent = source
        mesh.matrix_world = world
    bpy.data.objects.remove(character, do_unlink=True)
    character = source
    prefix = next(b.name for b in source.data.bones if b.name.endswith('RightHand'))[:-9]
    scene.frame_set(int(action.frame_range[0]))
    bpy.context.view_layer.update()
    hand = source.matrix_world @ source.pose.bones[prefix + 'RightHand'].matrix
    joint = lambda name: hand.inverted() @ source.matrix_world @ source.pose.bones[prefix + name].head
    index = joint('RightHandIndex2')
    pinky = joint('RightHandPinky2')
    axis = (index - pinky).normalized()
    centre = (index + pinky) * 0.5
    side = (joint('RightHandMiddle1') - joint('RightHand')).normalized()
    side = (side - axis * side.dot(axis)).normalized()
    normal = axis.cross(side).normalized()
    unit = 1.0 / hand.to_scale().x
    vertices = [centre + axis * a * unit + side * x * unit + normal * y * unit
                for a in (-0.12, 0.85) for x in (-0.025, 0.025) for y in (-0.005, 0.005)]
    data = bpy.data.meshes.new('SwordStandin')
    data.from_pydata(vertices, [], [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)])
    sword = bpy.data.objects.new('SwordStandin', data)
    scene.collection.objects.link(sword)
    common.workbench_clay(scene)
    scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.single_color = (0.65, 0.65, 0.65)
    f0, f1 = action.frame_range
    count = 9 if 'Slash' in clip else 5
    out = project / 'review/g1_mixamo' / clip.replace(' ', '_')
    out.mkdir(parents=True, exist_ok=True)
    mesh_objects = [o for o in bpy.data.objects if o.type == 'MESH' and o is not sword]
    lo, hi = common.world_bounds(mesh_objects)
    centre = (lo + hi) * 0.5
    height = max(hi.z - lo.z, 2.5) * 1.45
    print('SOURCE_BOUNDS', clip, list(lo), list(hi), flush=True)
    for view in rows:
        row = []
        for i in range(count):
            frame = f0 + (f1 - f0) * i / (count - 1)
            scene.frame_set(int(frame), subframe=frame % 1)
            sword.matrix_world = source.matrix_world @ source.pose.bones[prefix + 'RightHand'].matrix
            path = common.render_views(str(out / str(i)), centre.z, height, views=(view,),
                                       resolution=(260, 390), target=(centre.x, centre.y))[0]
            row.append([path, f'{clip} {frame:.0f} (mirror L at retarget)'])
        rows[view].append(row)
    report[clip] = {'source': str(library / (clip + '.fbx')), 'frames': [f0, f1],
                    'fps': scene.render.fps / scene.render.fps_base,
                    'source_rest_error_m': max(errors)}
for view, data in rows.items():
    out = project / 'review' / ('g1_mixamo_' + view)
    out.mkdir(exist_ok=True)
    (out / 'frames.json').write_text(json.dumps(data))
(project / 'review/g1_mixamo_sources.json').write_text(json.dumps(report, indent=2))
