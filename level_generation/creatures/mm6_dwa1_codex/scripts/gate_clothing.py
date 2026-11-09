import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot.blend'));roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget'];picks=[f'{n}:{f}'for n in roles for f in range(0,int(bpy.data.actions[n].frame_range[1])+1,2)]
sys.argv=['g4_weights.py','--',str(P/'work/pilot.blend'),'clothing',*picks];runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__')
