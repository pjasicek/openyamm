import bpy,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['textured_master','textured_master_full']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{name}.blend'));old=bpy.data.actions.get('Cast')
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions['Attack'].copy();a.name='Cast';a.use_fake_user=True;bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{name}.blend'))
f=P/'work/animation_audit.json';d=json.loads(f.read_text());d['Cast']=d['Attack'].copy();f.write_text(json.dumps(d,indent=2))
runpy.run_path(str(P/'scripts/export_genie.py'),run_name='__main__')
