from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for view in ('front','left','three_quarter'):
 sys.argv=['sheet','--',str(p/'work/full_timed.blend'),str(p/'review/full_motion'/view),view,'7','Attack','Running','Hit','Death','Fidget'];runpy.run_path(str(p/'scripts/clip_sheet.py'),run_name='__main__')
