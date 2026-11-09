import runpy
from pathlib import Path
p=Path(__file__).parent
for n in ['round1_render_export','round1_lod_visual']:runpy.run_path(str(p/(n+'.py')),run_name='__main__')
