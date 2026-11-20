"""Fit and measure one boss role before rebuilding the whole shell/export chain."""
from pathlib import Path
import runpy
import sys
P = Path(__file__).resolve().parents[1]
role = sys.argv[sys.argv.index('--')+1]
clip_role = 'Attack' if role.startswith('2Hand') else role
for name, args in [('forge_motion.py', [role]),
                   ('bake_new_twists.py', [P/'work/forge_motion.blend', P/'work/forge_motion.blend']),
                   ('gates.py', [P/'work/forge_motion.blend', 'forge_probe', 'Forge_'+clip_role]),
                   ('jerk_probe.py', [P/'work/forge_motion.blend', 'Forge_'+clip_role])]:
    sys.argv = [name, '--', *map(str, args)]
    runpy.run_path(str(P/'scripts'/name), run_name='__main__')
if clip_role == 'Attack':
    print('SOURCE JERK: unmodified library retarget',flush=True)
    sys.argv = ['jerk_probe.py','--',str(P/'work/forge_raw.blend'),'Forge_Attack']
    runpy.run_path(str(P/'scripts/jerk_probe.py'),run_name='__main__')
