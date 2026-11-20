"""Save an editable Hulk assembly from the final viewer GLB; authoritative rebuild sources are the scripts."""
import bpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/drudge_c.glb'))
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/hes_drudge.blend'))
print('EDITABLE_MASTER',len(bpy.data.actions),'actions',flush=True)
sys.stderr.flush();os._exit(0)
