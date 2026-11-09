"""G1 source motion study: original mannequin with a native-proportioned sword stand-in."""
from pathlib import Path
import runpy, sys
p=Path(__file__).resolve().parents[1]
clips=['2HandSwordAttack1','2HandSwordAttack6','2HandSwordAttack7','2HandSwordAttack9','2HandSwordIdle','2HandSwordWalk','2HandSwordGetHitF1','2HandSwordDeath1','2HandSwordIdleAlert1']
source=Path('anim_library/humanoid_set/2Hand Sword.glb').resolve()
assert source.is_file()
for view in ['front','left','three_quarter']:
    out=p/'review/g1'/view
    sys.argv=['source_preview.py','--',str(source),str(out),view,'7',*clips]
    runpy.run_path(str(p/'scripts/source_preview.py'),run_name='__main__')
    assert len(list(out.glob('*.png')))==len(clips)*7
