from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];s=p/'scripts/diagnose_uv.py';sys.argv=[str(s),'--',str(p/'work/rig_surface.blend'),str(p/'meshy/body_retexture_v1'),str(p/'work/unused.blend')];runpy.run_path(str(s),run_name='__main__')
