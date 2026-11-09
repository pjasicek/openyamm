from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for name in ('clip_timing.py','mace.py'):
 runpy.run_path(str(p/'scripts'/name),run_name='__main__')
for view in ('front','left','three_quarter'):
 sys.argv=[str(p/'scripts/clip_sheet.py'),'--',str(p/'work/rig_v7.blend'),str(p/f'review/native_{view}'),view,'7','Standing','Fidget','Attack','Death','Dead']
 runpy.run_path(sys.argv[0],run_name='__main__')
