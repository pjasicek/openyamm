"""Bake short-range cavity shading on the final body UV layout."""
import bpy
import os
import runpy
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/rig_uv_clean.blend'))
sys.argv=['bake','--','Hound',str(PROJECT/'textures/hound_ao.png'),'.04','2048']
runpy.run_path(str(PROJECT.parent/'claude_shared/bake_creature_ao.py'))
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
