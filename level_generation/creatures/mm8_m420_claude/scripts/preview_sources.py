from pathlib import Path
import runpy,sys,json
p=Path(__file__).resolve().parents[1];repo=p.parents[2];script=p/'scripts/source_preview.py'
for group,clips in [('Armed',['ArmedCastRAttack1','ArmedCastRAttack2','ArmedCastRAttackHand1']),('2Hand Staff',['StaffCastLAttack1','StaffCastLAttack3']),('Unarmed',['UnarmedCastDualAttack2','UnarmedGetHitF1','UnarmedDeath1'])]:
 for view in ['front','left','three_quarter']:
  out=p/'review/g1'/group/view
  sys.argv=[str(script),'--',str(repo/'anim_library/humanoid_set'/f'{group}.glb'),str(out),view,'7',*clips]
  runpy.run_path(str(script),run_name='__main__')
  rows=json.loads((out/'frames.json').read_text());assert len(rows)==len(clips)
