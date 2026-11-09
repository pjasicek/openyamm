import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.argv=['probe_uv.py','--',str(p/'work/texture_master.blend'),str(p/'meshy/retexture_v1'),str(p/'work/not_saved.blend')];runpy.run_path(str(p/'scripts/probe_uv.py'),run_name='__main__')
