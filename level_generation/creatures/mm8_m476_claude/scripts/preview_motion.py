from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for view in ['front','left']:
    s=p/'scripts/clip_sheet.py';sys.argv=[str(s),'--',str(p/'work/motion_v1.blend'),str(p/'review'/('motion_v1_'+view)),view,'5','Standing','Walking','Running','Attack','Hit','Fidget','Death'];runpy.run_path(str(s),run_name='__main__')
