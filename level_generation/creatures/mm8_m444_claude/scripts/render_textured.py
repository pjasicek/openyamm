from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];shared=p.parent/'claude_shared/render_glb_views.py'
sys.argv=[str(shared),'--',str(p/'review/viewer/mm8_m444_a.glb'),str(p/'review/textured'),'-y','800'];runpy.run_path(str(shared),run_name='__main__')
