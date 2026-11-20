import bpy,runpy,sys,os,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));from refit_lower_coat import refit
# Actual grip already passed; this round changes only the hidden trouser/coat layers.
for level in [2,3]:
 bpy.ops.wm.open_mainfile(filepath=str(p/f'work/final_lod{level}.blend'));refit(bpy.data.objects['Body']);name=f'work/refit_lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p/name));os.environ['GATE_BLEND']=name;os.environ['CLOTH_REPORT']=f'review/reduction/refit_lod{level}_cloth.json';runpy.run_path(str(p/'scripts/cloth_surface_gate.py'),run_name='__main__')
 d=json.loads((p/os.environ['CLOTH_REPORT']).read_text())['clips'];assert all(row['pass'] for row in d.values()),level
