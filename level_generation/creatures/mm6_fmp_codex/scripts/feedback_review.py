import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for file,label in [('review/feedback_v3/before/textured_uv.blend','before'),('work/feedback_contacts.blend','candidate')]:
 sys.argv=['clip_sheet.py','--',str(P/file),str(P/f'review/feedback_v3/{label}_motion'),'three_quarter','9','Death','Hit','Standing','Fidget']
 runpy.run_path(str(P/'scripts/clip_sheet.py'),run_name='__main__')
