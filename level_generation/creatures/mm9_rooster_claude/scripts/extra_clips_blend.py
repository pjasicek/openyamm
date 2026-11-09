"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/uv_v1c.blend), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the
installed clips, never grafted); holds are temporary corpses for the floor pass. Written by
claude_shared/make_extra_clips.py from scripts/extra_clips.json; run by scripts/extra_clips.sh.
Floor as build_runtime.sh: ground-loop for the fidget, raise for the hit (low-passed 0.06 s), Death2 grounded on a
temporary Dead2 (low-passed 0.08 s)."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Fidget2': (['Fidget2'], False),
    'Hit2': (['Wince2'], False),
    'Death2': (['Die2'], False),
    'Ctl_Fidget': (['Fidget1'], False),
    'Ctl_Hit': (['Wince1'], False),
    'Ctl_Death': (['Die1'], False),
}



X.main(HERE, ROLES, rig_name='MM9_Rig', holds={'Dead2': 'Death2', 'Ctl_Dead': 'Ctl_Death'}, hold_mode='eval')
