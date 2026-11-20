"""Focused exported Death/Dead checks during correction; full gates run again on final delivery."""
from pathlib import Path
import runpy
import sys
p = Path(__file__).resolve().parents[1]
sys.argv = [str(p / 'scripts/export_pilot.py'), '--', 'rig_finished_motion.blend', 'finished_motion']
runpy.run_path(str(p / 'scripts/export_pilot.py'), run_name='__main__')
sys.path.insert(0, str(Path('level_generation/creatures/claude_shared/gates').resolve()))
import run_gates as gates
all_clips = gates.Glb.clips
gates.Glb.clips = lambda self: [row for row in all_clips(self) if row[0] in ('Death', 'Dead')]
sys.argv = ['run_gates.py', '--', str(p / 'export/finished_motion_body.glb'),
            '--config', str(p / 'finished_motion.gates.json'), '--out', str(p / 'review/death_finish_gates')]
gates.main()
