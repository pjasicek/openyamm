from pathlib import Path
import bpy,sys,runpy,os
p=Path(__file__).resolve().parents[1]
blend=p/'work/rig_ready.blend';acts=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
bpy.ops.wm.open_mainfile(filepath=str(blend))
picks=[f'{n}:{f}' for n in acts for f in range(0,int(bpy.data.actions[n].frame_range[1])+1,2)]
sys.argv=['g4','--',str(blend),'ready']+picks
runpy.run_path(str(p/'scripts/g4_weights.py'),run_name='__main__')
os.environ['STEP']='0.5'
for name in ('g5_hand_stretch.py','sole_probe.py','jerk_probe.py','g6_ratman.py'):
 sys.argv=[name,'--',str(blend)]+acts;runpy.run_path(str(p/'scripts'/name),run_name='__main__')
