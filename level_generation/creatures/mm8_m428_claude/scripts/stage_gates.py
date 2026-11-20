"""Driver: arm/hand gate numbers on the final rig (work/rig_sim.blend): G4 weights at sampled frames of every clip,
G5 hand stretch, soles, jerk; plus textured Fidget/Hit/Running frames from the textured master."""
import runpy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
def run(n, *a):
    sys.argv = [n, '--', *[str(x) for x in a]]; runpy.run_path(str(P / 'scripts' / n), run_name='__main__')
import os
B = P / os.environ.get('GATE_BLEND', 'work/rig_textured_uv.blend')   # the textured master: final mesh, weights, clips
frames = {'Standing': (0, 30, 60), 'Walking': (0, 6, 12, 18), 'Running': (0, 6, 12, 17), 'Hit': (4, 8, 12),
          'Death': (10, 20, 39), 'Fidget': (0, 15, 25, 35, 45, 55)}
run('g4_weights.py', B, 'final', *[f'{a}:{f}' for a, fs in frames.items() for f in fs])
run('jerk_probe.py', B, 'Standing', 'Walking', 'Running', 'Hit', 'Death', 'Fidget')
run('g5_hand_stretch.py', B, 'Standing', 'Walking', 'Running', 'Hit', 'Death', 'Fidget')
run('sole_probe.py', B, 'Standing', 'Walking', 'Running', 'Hit', 'Death', 'Fidget')
