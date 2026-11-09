import os,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
os.environ['GATE_BLEND']='work/review4_lod3.blend';os.environ['PENETRATION_REPORT']='review/round4/penetration_lod3.json';os.environ.pop('PENETRATION_PROBE',None)
runpy.run_path(str(p/'scripts/review4_penetration.py'),run_name='__main__')
os.environ['LOD_REVIEW']='1';os.environ['LOD_LEVEL']='3'
runpy.run_path(str(p/'scripts/review4_reduction_render.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/review4_render_final.py'),run_name='__main__')
