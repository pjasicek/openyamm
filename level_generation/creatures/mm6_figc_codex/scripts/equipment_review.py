import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/equipment.py'),run_name='__main__')
for view in ['front','left','three_quarter']:
 sys.argv=['clip_sheet.py','--',str(P/'work/equipped.blend'),str(P/f'review/equipped_{view}'),view,'5','Standing','Walking','Running','Attack','Hit','Fidget','Death'];runpy.run_path(str(P/'scripts/clip_sheet.py'),run_name='__main__')
