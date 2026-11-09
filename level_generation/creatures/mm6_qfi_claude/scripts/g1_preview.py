"""G1: candidate Mixamo clips for the queen's upper body, on the library's own mannequin (Warrok), before modelling.
Writes review/g1/<clip>_<i>_<view>.png and review/g1/frames.json (rows for compose_sheet).
Candidates: work/g1_candidates.json {"view": ..., "frames": n, "clips": [names under anim_library/mixamo, no .fbx]}."""
import bpy, sys, json
from pathlib import Path
p = Path(__file__).resolve().parents[1]
repo = p.parents[2]
sys.path.insert(0, str(p / 'scripts'))
import common
config = json.loads((p / 'work' / 'g1_candidates.json').read_text())
view, n, names = config['view'], config['frames'], config['clips']
out = p / 'review' / 'g1'
out.mkdir(parents=True, exist_ok=True)
rows = []
for name in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(repo / 'anim_library/mixamo/characters/warrok_w_kurniawan.fbx'))
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(repo / 'anim_library/mixamo' / (name + '.fbx')))
    source = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
    act = source.animation_data.action
    arm.animation_data_create()
    arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o, do_unlink=True)
    scene = bpy.context.scene
    common.workbench_clay(scene)
    scene.frame_set(1)
    lo, hi = common.world_bounds(meshes)
    h = hi.z - lo.z
    f0, f1 = act.frame_range
    row = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(n - 1, 1)
        scene.frame_set(int(f), subframe=f % 1)
        prefix = out / f'{name.replace(" ", "_")}_{i}'
        files = common.render_views(str(prefix), (lo.z + hi.z) / 2, h * 1.25, views=(view,), resolution=(200, 300),
                                    target=((lo.x + hi.x) / 2, (lo.y + hi.y) / 2))
        row.append([files[0], f'{name} {(f - f0) / 30:.2f}s'])
    rows.append(row)
(out / f'frames_{view}.json').write_text(json.dumps(rows) + '\n')
