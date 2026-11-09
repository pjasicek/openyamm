"""G1 for the gait2 walk and run (2026-10-21): retarget Mixamo walk/run candidates onto the textured rig master
(scratch work/gait2_candidates.blend), so their stride on our body and their look can be compared before choosing."""
from pathlib import Path
import runpy, sys
p = Path(__file__).resolve().parents[1]; lib = p.parents[2] / 'anim_library/mixamo'
items = [f'{lib}/{f}.fbx:{n}' for f, n in [('Walk', 'C_Walk'), ('Walking (10)', 'C_Walking10'), ('Walking (16)', 'C_Walking16'),
         ('Walking (9)', 'C_Walking9'), ('Standard Walk', 'C_StandardWalk'), ('Run', 'C_Run'), ('Running (4)', 'C_Running4'),
         ('Run Forward (2)', 'C_RunForward2'), ('Slow Run', 'C_SlowRun'), ('Standard Run', 'C_StandardRun')]]
s = p / 'scripts/gait2_retarget_mixamo.py'
sys.argv = [str(s), '--', str(p / 'work/rig_textured_uv.blend'), str(p / 'work/gait2_candidates.blend'), *items]
runpy.run_path(str(s), run_name='__main__')
