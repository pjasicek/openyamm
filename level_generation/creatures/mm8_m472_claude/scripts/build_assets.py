"""Rebuild final GLBs from the selected fitted/UV master; no generation or paid jobs."""
from pathlib import Path
import runpy,subprocess,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def python(script,*args):subprocess.run(['/usr/bin/python3',str(script),*map(str,args)],check=True)
runpy.run_path(str(p/'scripts/measure_stride.py'),run_name='__main__')
python(p/'scripts/compose_textures.py')
runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
python(repo/'tools/prepare_actor_glb.py',p/'export/mm8_m472_lod0.glb',p/'export/mm8_m472_prepared.glb')
runpy.run_path(str(p/'scripts/build_lods.py'),run_name='__main__')
python(p/'scripts/finish_runtime.py');python(p/'scripts/viewer_tiers.py')
