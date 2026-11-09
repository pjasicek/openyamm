"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/texpass/uv_final.blend), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the
installed clips, never grafted); holds are temporary corpses for the floor pass. Written by
claude_shared/make_extra_clips.py from scripts/extra_clips.json; run by scripts/extra_clips.sh.
Floor as build_runtime.sh: every living clip down 0.2289 (pass 1), then the tail strips lifted out of the floor and
the clip raised (pass 2). Breath2 is MM9's Rattack2 (the accepted Cast plays Rattack3, AttackRanged rAttack1)."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Fidget2': (['fidget2'], False),
    'SpitAcross': (['spitacross'], False),
    'Breath2': (['Rattack2'], False),
    'Hit2': (['wince2'], False),
    'Ctl_Fidget': (['fidget1'], False),
    'Ctl_Hit': (['wince1'], False),
    'Ctl_Cast': (['Rattack3'], False),
}



X.main(HERE, ROLES, rig_name='MM9_Rig', holds={}, hold_mode='eval')
