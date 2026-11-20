from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
sys.argv=[str(p/'scripts/reduce_rigged.py'),'--',str(p/'work/rig_v5.blend'),str(p/'work/rig_v5r.blend')];runpy.run_path(str(p/'scripts/reduce_rigged.py'),run_name='__main__')
sys.argv=[str(p/'scripts/export_uploads.py')];runpy.run_path(str(p/'scripts/export_uploads.py'),run_name='__main__')
