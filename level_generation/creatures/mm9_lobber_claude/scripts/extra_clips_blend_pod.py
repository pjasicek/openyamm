"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/uv_pod_v3.blend), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the
installed clips, never grafted); holds are temporary corpses for the floor pass. Written by
claude_shared/make_extra_clips.py from scripts/extra_clips.json; run by scripts/extra_clips.sh.
Floor as build_runtime.sh pod: gaits ground-looped, taunt and hit raised. projectile (the pod in flight, MM9 plays
it while the pod is a missile) is only raised (never under the floor); land ground-looped."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'Projectile': (['projectile'], True),
    'Land': (['land'], False),
    'Taunt': (['taunt'], False),
    'Hit2': (['wince2'], False),
    'Backpedal': (['Backpedal'], True),
    'BackpedalRun': (['BackpedalRun'], True),
    'Ctl_Fidget': (['fidget'], False),
    'Ctl_Walking': (['walk'], True),
    'Ctl_Hit': (['wince1'], False),
}

X.main(HERE, ROLES, rig_name='MM9_Rig', holds={}, hold_mode='rec')
