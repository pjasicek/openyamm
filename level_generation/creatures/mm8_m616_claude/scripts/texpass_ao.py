"""AO on the texture-pass UVs (2026-10-31): the same short-range bake as bake_ao.py (claude_shared/bake_creature_ao.py,
reach 18 mm, 2048 px), on the welded LOD0 of work/texpass/<uv blend>. Args: <uv blend> <out png>"""
import runpy
import sys
from pathlib import Path
import bpy

P = Path(__file__).resolve().parents[1]
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sys.argv = ['bake_creature_ao.py', '--', 'BoneDragon', argv[1], '.018', '2048']
runpy.run_path(str(P.parent / 'claude_shared/bake_creature_ao.py'), run_name='__main__')
