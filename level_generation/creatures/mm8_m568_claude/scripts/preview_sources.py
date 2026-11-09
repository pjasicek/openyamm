"""G1 comparison of owned two-hand spear sources, using the established prop preview."""
from pathlib import Path
import runpy, sys
P=Path(__file__).resolve().parents[1]
preview=P.parent/'mm6_natm_claude/scripts/spear_preview.py'
for view in ('front','left','three_quarter'):
    sys.argv=[str(preview),'--','anim_library/humanoid_set/2Hand Spear.glb',str(P/'review/source_motion'/view),view,'5','2HandSpearAttack1','2HandSpearAttack6']
    runpy.run_path(str(preview),run_name='__main__')
