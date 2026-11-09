from pathlib import Path
import bpy,sys,json,runpy
p=Path(__file__).resolve().parents[1]
for view in ['front','left','three_quarter']:
 s=p/'scripts/clip_sheet.py';sys.argv=[str(s),'--',str(p/'work/rig_animated.blend'),str(p/'review/motion'/view),view,'7','Standing','Walking','Attack','Hit','Death','Running','Fidget'];runpy.run_path(str(s),run_name='__main__')
