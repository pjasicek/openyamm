"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/uv_v3.blend), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources
(compared with the installed clips, never grafted); Dead2 / Ctl_Dead are temporary holds for the floor pass.
Run by scripts/extra_clips.sh."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Hang': (['hang'], True),
    'HangFidget': (['hangfidget'], False),
    'Launch': (['launch'], False),
    'AttackRanged2': (['attackair2'], False),
    'Hit2': (['winceair2'], False),
    'Death2': (['dieair2', 'fall2', 'FallDown2'], False),
    'Ctl_Fidget': (['fidgetair1'], False),
    'Ctl_Death': (['DieAir1', 'fall1', 'FallDown1'], False),
}
X.main(HERE, ROLES, rig_name='MM9_Rig', holds={'Dead2': 'Death2', 'Ctl_Dead': 'Ctl_Death'})
