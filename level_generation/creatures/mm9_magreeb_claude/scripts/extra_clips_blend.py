"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/uv_v8.blend), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the
installed clips, never grafted); holds are temporary corpses for the floor pass. Written by
claude_shared/make_extra_clips.py from scripts/extra_clips.json; run by scripts/extra_clips.sh.
Floor as build_runtime.sh: ground-loop for idles and gaits (Running is ground-looped there), raise for taunt, hit
and the Jumping loop (MM9 Jumping: a hop cycle with footsteps), Death2 grounded on a temporary Dead2.
MM9's Jumping carries exactly walk's keys (0.0000 deg): bound as jump: Walking, not grafted."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Fidget2': (['fidget2'], False),
    'Hit2': (['wince2'], False),
    'Death2': (['die2'], False),
    'Backpedal': (['Backpedal'], True),
    'BackpedalRun': (['Backpedalrun'], True),
    'Taunt': (['Taunt'], False),
    'Jump': (['Jumping'], True),
    'Ctl_Fidget': (['fidget1'], False),
    'Ctl_Hit': (['wince1'], False),
    'Ctl_Death': (['die1'], False),
}



X.main(HERE, ROLES, rig_name='MM9_Rig', holds={'Dead2': 'Death2', 'Ctl_Dead': 'Ctl_Death'}, hold_mode='rec')
