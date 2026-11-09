import bpy,runpy,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['reduce_rigged.py','--',str(p/'work/motion_final.blend'),str(p/'work/reduced_v1.blend')]
runpy.run_path(str(p/'scripts/reduce_rigged.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/export_uploads.py'),run_name='__main__')
for view in ('front','left'):
 sys.argv=['clip_sheet.py','--',str(p/'work/texture_ready.blend'),str(p/'review'/('reduced_'+view)),view,'5','Standing','Walking','Run','Hit','Death']
 runpy.run_path(str(p/'scripts/clip_sheet.py'),run_name='__main__')
