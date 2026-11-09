"""Check the local Mutant sources in an isolated Blender before selecting motion."""
import bpy
import json
import os
from pathlib import Path
import sys

p = Path(__file__).resolve().parents[1]
repo = p.parents[2]
paths = [repo / "anim_library/mixamo/characters/warrok_w_kurniawan.fbx",
         repo / "anim_library/mixamo/Mutant Idle.fbx"]
records = []
for path in paths:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path))
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    assert len(arms) == 1, (path, len(arms))
    arm = arms[0]
    records.append({"path": str(path.relative_to(repo)), "bones": list(arm.data.bones.keys()),
                    "scale": list(arm.scale), "meshes": [o.name for o in bpy.data.objects if o.type == "MESH"],
                    "actions": [{"name": a.name, "frames": list(a.frame_range)} for a in bpy.data.actions],
                    "fps": bpy.context.scene.render.fps})
(p / "review").mkdir(exist_ok=True)
(p / "review/source_inspection.json").write_text(json.dumps(records, indent=2) + "\n")
print(json.dumps(records, indent=2))
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
