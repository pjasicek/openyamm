import runpy,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['import_final.py','skirt_intersections.py','uv_gate.py','extra_gates.py']:
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'))
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_dwa1.blend'))
