"""Run the established far-LOD repair ladder on this uninstalled Hesper export."""
import os
import subprocess
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
PYTHON=PROJECT.parent/'hes_noble_bosses_claude/work/venv/bin/python'
env={**os.environ,'LOD_REPAIR_PYTHON':str(PYTHON),'PYTHONDONTWRITEBYTECODE':'1',
     'OPENBLAS_NUM_THREADS':'4','OMP_NUM_THREADS':'4','QT_QPA_PLATFORM':'offscreen'}
subprocess.run([str(PYTHON),'-B',str(PROJECT/'lodrep/repair_glb.py'),
    str(PROJECT/'work/hound_variants.glb'),str(PROJECT/'work/lod_repair'),
    str(PROJECT/'export/hes_hound.glb')],check=True,env=env)
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
