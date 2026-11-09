"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/uv_v3c.blend), and export the armature with them. AttackRanged2 is MM9's RAttack1 (the accepted AttackRanged
plays Hattack2). Ctl_* are controls rebuilt from accepted clips' sources (compared with the installed clips, never
grafted); Dead2 / Ctl_Dead are temporary holds for the floor pass. Run by scripts/extra_clips.sh."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Aware': (['aware'], True),
    'Taunt': (['taunt'], False),
    'Fidget2': (['fidget2'], False),
    'AttackRanged2': (['RAttack1'], False),
    'Hit2': (['wince2'], False),
    'Death2': (['die2'], False),
    'Backpedal': (['backpedal'], True),
    'BackpedalRun': (['backpedalrun'], True),
    'Ctl_Fidget': (['fidget1'], False),
    'Ctl_Hit': (['wince1'], False),
    'Ctl_Death': (['die1'], False),
}
X.main(HERE, ROLES, rig_name='MM9_Rig', holds={'Dead2': 'Death2', 'Ctl_Dead': 'Ctl_Death'})
