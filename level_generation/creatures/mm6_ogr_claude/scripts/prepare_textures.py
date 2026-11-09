from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/finish_clay.py'),run_name='__main__')
s=p/'scripts/g4_weights.py';sys.argv=[str(s),'--',str(p/'work/rig_v5t.blend'),'rings','Attack:20','Attack:28'];runpy.run_path(str(s),run_name='__main__')
runpy.run_path(str(p/'scripts/export_uploads.py'),run_name='__main__')
