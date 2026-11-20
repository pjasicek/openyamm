import bpy,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];blend=p/'work/rig_v5.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend));picks=[]
for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
 a=bpy.data.actions[name];picks.extend(f'{name}:{f}' for f in range(0,int(a.frame_range[1])+1,2))
sys.argv=['g4_weights.py','--',str(blend),'pilot',*picks]
runpy.run_path(str(p/'scripts/g4_weights.py'),run_name='__main__')
