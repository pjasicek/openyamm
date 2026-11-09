"""Editable snapshot of the verified runtime LOD0, including the corrected winding and material variants."""
from pathlib import Path
import bpy
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P/'export/hes_bulwark.glb'))
bpy.context.scene.frame_set(0)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/hes_bulwark.blend'))
print('EDITABLE MASTER SAVED',flush=True)
