import bpy,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for n in ['review_renders.py','render_props.py']:
 runpy.run_path(str(P/'scripts'/n),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_authoring.blend'));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_authoring.blend'))
