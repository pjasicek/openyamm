"""Retarget the reviewed owned walk with the shared source-frame implementation."""
import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['retarget_mixamo','--',str(P/'work/rig_v6.blend'),str(P/'work/walk_raw_v6.blend'),'anim_library/mixamo/Mutant Walking.fbx:Walking']
runpy.run_path('level_generation/creatures/mm6_bar1_claude/scripts/retarget_mixamo.py',run_name='__main__')
