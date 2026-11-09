"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export_v2.py opens, and
export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the installed
clips, never grafted). Run by scripts/extra_clips.sh."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Spawn': (['spawn'], False),
    'Taunt': (['taunt'], False),
    'Fidget2': (['fidget2'], False),
    'Block': (['block'], False),
    'AttackMelee2': (['Hattack2'], False),
    'DodgeLeft': (['dodgeleft'], False),
    'DodgeRight': (['dodgeright'], False),
    'Hit2': (['wince2'], False),
    'Backpedal': (['Backpedal'], True),
    'BackpedalRun': (['Backpedalrun'], True),
    'Ctl_Fidget': (['fidget1'], False),
    'Ctl_Walking': (['walk'], True),
    'Ctl_AttackMelee': (['Hattack1'], False),
}
X.main(HERE, ROLES, rig_name='MM9_Rig')
