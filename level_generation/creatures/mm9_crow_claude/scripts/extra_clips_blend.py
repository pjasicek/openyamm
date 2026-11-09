"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/graft_v7.blend), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the
installed clips, never grafted); holds are temporary corpses for the floor pass. Written by
claude_shared/make_extra_clips.py from scripts/extra_clips.json; run by scripts/extra_clips.sh.
Flier rule as build_runtime.sh: hover 0.4252 on every living clip, Death2 eases it out and is grounded on a temporary
Dead2. MM9's stand and fidget1 are the crow on the ground (Perch, PerchFidget): ground-looped after the hover so its
feet are on the floor. A new living clip still under the floor takes one --raise-uniform lift."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Perch': (['stand'], True),
    'PerchFidget': (['fidget1'], False),
    'Hit2': (['winceair2'], False),
    'Death2': (['dieair2', 'fall2', 'falldown2'], False),
    'Ctl_Fidget': (['fidgetAir1'], False),
    'Ctl_Death': (['dieair1', 'fall1', 'falldown1'], False),
}



X.main(HERE, ROLES, rig_name='MM9_Rig', holds={'Dead2': 'Death2', 'Ctl_Dead': 'Ctl_Death'}, hold_mode='eval')
