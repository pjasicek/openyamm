"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/uv_lobber_v4.blend), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the
installed clips, never grafted); holds are temporary corpses for the floor pass. Written by
claude_shared/make_extra_clips.py from scripts/extra_clips.json; run by scripts/extra_clips.sh.
Floor as build_runtime.sh lobber: every living clip ground-looped (the root bulb on the floor).
Left out: MM9 fall1 and falldown1, the drop from the ceiling. Our Lobber grows upright from the floor (README), so the
fall would rise; its Death is DieAir1 then a wilt, as accepted."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Fidget2': (['FidgetAir2'], False),
    'Aware': (['AwareAir'], True),
    'Hit2': (['winceAir1'], False),
    'Ctl_Fidget': (['FidgetAir1'], False),
    'Ctl_Hit': (['winceAir2'], False),
}

X.main(HERE, ROLES, rig_name='MM9_Rig', holds={}, hold_mode='rec')
