"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
(work/uv_v8.blend), and export the armature with them. Wince2 and returntocrouch were only inside the stitched Death;
they are added on their own too. Ctl_* are controls rebuilt from accepted clips' sources (compared with the installed
clips, never grafted). Run by scripts/extra_clips.sh."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {
    'CrouchedAware': (['CrouchedAware'], True),
    'Crouch': (['crouch'], True),
    'CrouchFidget': (['crouchfidget'], False),
    'ReturnToCrouch': (['returntocrouch'], False),
    'Walk2': (['Walk1'], True),
    'Taunt': (['Taunt'], False),
    'Search': (['Search'], False),
    'AttackMelee2': (['HAttack2'], False),
    'Jump': (['Jump'], False),
    'Hit2': (['Wince2'], False),
    'Ctl_Fidget': (['Fidget1'], False),
    'Ctl_Walking': (['Walk'], True),
    'Ctl_AttackMelee': (['HAttack1'], False),
}
X.main(HERE, ROLES, rig_name='MM9_Rig')
