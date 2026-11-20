"""G1: preview owned two-hand casting clips on their source mannequin before body modelling."""
from pathlib import Path
import json
import math
import sys
import bpy

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / "mm6_natm_claude/scripts"))
import common

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(REPO / "anim_library/humanoid_set/Unarmed.glb"))
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
rig.rotation_mode = "XYZ"
rig.rotation_euler.z = math.pi
for obj in bpy.data.objects:
    if obj.type == "MESH" and obj.parent is not rig:
        obj.hide_render = True
bpy.context.view_layer.update()
scene = bpy.context.scene
common.workbench_clay(scene)
source_fps = scene.render.fps / scene.render.fps_base
candidates = ["UnarmedCastDualAOE1", "UnarmedCastDualAttack1",
              "UnarmedCastDualAttack3", "UnarmedCastDualSummon1", "UnarmedGetHitF1"]
acts = {x.name.split("@")[-1].split("|")[-1]: x for x in bpy.data.actions}
out = PROJECT / "review/motion_source"
out.mkdir(exist_ok=True)
report = []
rows = []
for name in candidates:
    act = acts.get(name) or next(x for k, x in acts.items() if k.endswith(name))
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    start, end = act.frame_range
    assert end > start
    report.append({"clip": name, "source_fps": source_fps, "duration": (end-start)/source_fps})
    for view in ("front", "left", "three_quarter"):
        row = []
        for i in range(6):
            frame = start + (end-start)*i/5
            scene.frame_set(int(frame), subframe=frame-int(frame))
            file = common.render_views(str(out / f"{name}_{i}"), 1.5, 2.9,
                                       views=(view,), resolution=(220, 300))[0]
            row.append([file, f"{name} {view} {((frame-start)/source_fps):.2f}s"])
        rows.append(row)
(out / "frames.json").write_text(json.dumps(rows, indent=2) + "\n")
(out / "clips.json").write_text(json.dumps(report, indent=2) + "\n")
assert len(rows) == len(candidates)*3
print("G1 source motion frames:", len(rows)*6, flush=True)
