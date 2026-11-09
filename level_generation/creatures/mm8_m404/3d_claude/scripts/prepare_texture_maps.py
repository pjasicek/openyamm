"""Rasterise both retained UV sets and bake their short-range AO with the existing project tools."""
from pathlib import Path
import runpy
import sys
p = Path(__file__).resolve().parents[1]
master = str(p / 'work/rig_textured.blend')
for layer in ('UVMap', 'HeadUV'):
    sys.argv = ['uv_raster.py', '--', master, layer, '1024']
    runpy.run_path(str(p / 'scripts/uv_raster.py'), run_name='__main__')
sys.argv = ['bake_ao.py', '--', master, '1024']
runpy.run_path(str(p / 'scripts/bake_ao.py'), run_name='__main__')
