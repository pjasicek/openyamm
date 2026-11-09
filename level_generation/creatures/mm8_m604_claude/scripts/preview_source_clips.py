"""Review the owned sword clips on their source mannequin before modelling."""
from pathlib import Path
import runpy
import sys

repo = Path(__file__).resolve().parents[4]
project = Path(__file__).resolve().parents[1]
preview = repo / 'level_generation/creatures/mm6_bar1_claude/scripts/rpg_preview.py'
clips = ['SwordAttackR2', 'SwordAttackR5', 'SwordAttackR6', 'SwordAttackR7']
for view in ('front', 'left', 'three_quarter'):
    out = project / 'review/g1_overhead' / view
    sys.argv = [str(preview), '--', str(repo / 'anim_library/humanoid_set/1Hand.glb'),
                str(out), view, '6', *clips]
    runpy.run_path(str(preview), run_name='__main__')
    assert len(list(out.glob('*.png'))) == len(clips) * 6
