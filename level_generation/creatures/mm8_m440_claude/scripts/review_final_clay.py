from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for view in ('front','left','three_quarter'):
 sys.argv=['sheet','--',str(p/'work/full_repaired.blend'),str(p/'review/final_clay'/view),view,'5','Standing','Walking','Attack','Running','Hit','Death','Fidget'];runpy.run_path(str(p/'scripts/clip_sheet.py'),run_name='__main__')
