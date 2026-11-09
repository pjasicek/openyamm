"""Preview owned Mixamo candidates on their original Warrok mannequin, before modelling."""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / 'mm6_natm_claude/scripts'))
import common

OUT = PROJECT / 'motion/source_previews'
OUT.mkdir(parents=True, exist_ok=True)
CANDIDATES = ['Standard Idle', 'Orc Walk', 'Mutant Walking', 'Running (5)',
              'Throw Object', 'Standing React Small From Front', 'Mutant Dying', 'Orc Idle (1)',
              '_discarded/Throw In', 'Lifting Object', 'Bash']
report = json.loads((OUT / 'candidates.json').read_text()) if (OUT / 'candidates.json').exists() else {}
for stem in CANDIDATES:
    if stem in report:
        continue
    label = Path(stem).name
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(REPO / 'anim_library/mixamo/characters/warrok_w_kurniawan.fbx'))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    assert meshes
    before = set(bpy.data.objects)
    path = REPO / 'anim_library/mixamo' / (stem + '.fbx')
    bpy.ops.import_scene.fbx(filepath=str(path))
    objects = set(bpy.data.objects) - before
    source = next(o for o in objects if o.type == 'ARMATURE')
    action = source.animation_data.action
    assert set(source.data.bones.keys()) == set(rig.data.bones.keys()), stem
    # Fit the preview mannequin's rest skin onto this clip's own source skeleton.
    transforms = {n: (source.matrix_world @ source.data.bones[n].matrix_local)
                  @ (rig.matrix_world @ rig.data.bones[n].matrix_local).inverted()
                  for n in source.data.bones.keys()}
    for mesh in meshes:
        world = mesh.matrix_world.copy()
        groups = {g.index: g.name for g in mesh.vertex_groups}
        for vertex in mesh.data.vertices:
            old = world @ vertex.co
            weights = [(transforms[groups[g.group]], g.weight) for g in vertex.groups
                       if groups[g.group] in transforms and g.weight > 0]
            total = sum(w for _, w in weights)
            assert total > .99
            vertex.co = sum((matrix @ old * (weight / total) for matrix, weight in weights), Vector())
        mesh.parent = None
        mesh.matrix_world.identity()
        for mod in mesh.modifiers:
            if mod.type == 'ARMATURE':
                mod.object = source
    bpy.data.objects.remove(rig, do_unlink=True)
    rig = source
    scene = bpy.context.scene
    common.workbench_clay(scene)
    scene.render.fps = 30
    start, end = action.frame_range
    row = {'file': str(path.relative_to(REPO)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
           'frame_range': [start, end], 'fps': 30, 'duration': (end - start) / 30, 'images': [], 'joints': []}
    for i in range(7):
        frame = start + (end - start) * i / 6
        scene.frame_set(int(frame), subframe=frame % 1)
        lo, hi = common.world_bounds(meshes)
        center = (lo + hi) / 2
        files = common.render_views(str(OUT / f'{label}_{i}'), center.z, max(2.4, hi.z - lo.z + .4),
                                    views=('front', 'left', 'three_quarter'), resolution=(240, 320),
                                    target=(center.x, center.y))
        row['images'].append(files)
        row['joints'].append({b.name: list(rig.matrix_world @ b.head) for b in rig.pose.bones
                              if any(k in b.name for k in ('Hand', 'Foot', 'Head', 'Hips'))})
    assert len(row['images']) == 7
    report[stem] = row
    print('PREVIEW', stem, row['duration'], flush=True)
(OUT / 'candidates.json').write_text(json.dumps(report, indent=2) + '\n')
assert len(report) == len(CANDIDATES)
