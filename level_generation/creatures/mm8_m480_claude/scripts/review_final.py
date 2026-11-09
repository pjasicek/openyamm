from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for tier in 'abc':
 s=p/'scripts/render_tex.py';sys.argv=[str(s),'--',str(p/'work/ready_final.blend'),str(p/f'textures/m480_{tier}_preview.png'),f'native_tier_{tier}',str(p/f'textures/m480_head_{tier}_preview.png')];runpy.run_path(str(s),run_name='__main__')
s=p/'scripts/final_mesh_checks.py';sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
