"""Check isolated Blender and glTF availability before paying for geometry."""
import bpy
import json
import os
from pathlib import Path
import sys

assert bpy.app.background
assert hasattr(bpy.ops.import_scene, "gltf") and hasattr(bpy.ops.export_scene, "gltf")
p = Path(__file__).resolve().parents[1] / "review"
p.mkdir(exist_ok=True)
(p / "blender_preflight.json").write_text(json.dumps({"version": bpy.app.version_string,
    "background": bpy.app.background, "gltf": True}, indent=2) + "\n")
print("Isolated Blender and glTF preflight passed", flush=True)
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
