"""Prepare runtime textures and build body LOD1/shadows before the far-LOD texture repair."""
import os
import subprocess
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
REPO=PROJECT.parents[2]
sys.path.insert(0,str(REPO/'tools'))
from build_actor_lods import generate
subprocess.run(['/usr/bin/python3',str(REPO/'tools/prepare_actor_glb.py'),
    str(PROJECT/'export/hes_hound_raw.glb'),str(PROJECT/'work/hound_prepared.glb')],check=True)
generate(PROJECT/'work/hound_prepared.glb',PROJECT/'work/hound_lods.glb','Hound',
         ratios=(.5,.25,.125),max_influences=4)
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
