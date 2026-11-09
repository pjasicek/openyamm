"""Preview local candidate motions on their source mannequin before modelling."""
from pathlib import Path
import bpy
import json
import math
import sys

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[2]
sys.path.insert(0, str(REPO / "level_generation/creatures/mm6_natm_claude/scripts"))
import common

candidates = {
    "Armed": ["ArmedCastRAttackHand1", "ArmedCastLAttackHand2", "ArmedWalk"],
    "Unarmed": ["UnarmedIdle", "UnarmedRunForward", "UnarmedAttackR3", "UnarmedGetHitF1", "UnarmedDeath1"],
}
out = PROJECT / "motion/source_preview"
out.mkdir(parents=True, exist_ok=True)
rows = []
measurements = []
for library, names in candidates.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    source = REPO / "anim_library/humanoid_set" / (library + ".glb")
    bpy.ops.import_scene.gltf(filepath=str(source))
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    arm.rotation_mode = "XYZ"
    arm.rotation_euler = (0, 0, math.pi)
    for obj in bpy.data.objects:
        if obj.type == "MESH" and obj.parent is not arm:
            obj.hide_render = True
    common.workbench_clay(scene)
    actions = {a.name.split("@")[-1].split("|")[-1]: a for a in bpy.data.actions}
    for name in names:
        matches = [a for key, a in actions.items() if key.endswith(name)]
        assert len(matches) == 1, (name, list(actions))
        action = matches[0]
        arm.animation_data.action = action
        if action.slots:
            arm.animation_data.action_slot = action.slots[0]
        start, end = action.frame_range
        assert end > start
        measurements.append({"source": str(source.relative_to(REPO)), "clip": name,
                             "frames": [start, end], "fps": 30, "duration": (end-start)/30})
        for view in ["front", "left", "three_quarter"]:
            row = []
            for i in range(5):
                frame = start + (end-start)*i/4
                scene.frame_set(int(frame), subframe=frame-int(frame))
                path = common.render_views(str(out / f"{name}_{i}"), 1.2, 3.0,
                                           views=(view,), resolution=(192, 280))[0]
                row.append([path, f"{name} {view} {frame:.1f}"])
            rows.append(row)
(out / "frames.json").write_text(json.dumps(rows, indent=2)+"\n")
(PROJECT / "motion/source_preview.json").write_text(json.dumps(measurements, indent=2)+"\n")
print("Previewed", len(measurements), "source clips")
