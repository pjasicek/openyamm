from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];sys.argv=['uv','--',str(p/'work/rig_uv_master.blend'),str(p/'meshy/body_retexture_v1'),str(p/'work/unused.blend')];runpy.run_path(str(p/'scripts/diagnose_uv.py'),run_name='__main__')
