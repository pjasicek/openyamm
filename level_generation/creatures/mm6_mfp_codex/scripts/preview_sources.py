import sys,runpy,os,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]; ROOT=P.parents[2];sys.dont_write_bytecode=True
sys.path.insert(0,str(P/'scripts'));os.chdir(ROOT)
roles={'Standing':('Relax','RelaxIdle'),'Walking':('Relax','RelaxWalkFemale3'),'Running':('Relax','RelaxRunForward'),'Attack':('1Hand','DaggerAttackR2'),'Death':('Relax','RelaxLaydownLayDown'),'Hit':('Unarmed','UnarmedGetHitF1')}
def run(f,args):
 sys.argv=[f,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/f),run_name='__main__')
run('source_rest.py',[ROOT/'anim_library/humanoid_set/Armed.glb'])
for st,clips in [('1Hand',['DaggerAttackR1','DaggerAttackR2','DaggerAttackR3']),('Relax',['RelaxIdle','RelaxWalkFemale3','RelaxRunForward','RelaxLaydownLayDown']),('Unarmed',['UnarmedGetHitF1'])]:
 for view in ['front','left','three_quarter']:
  run('rpg_preview.py',[ROOT/f'anim_library/humanoid_set/{st}.glb',P/f'review/g1/{st}/{view}',view,'6',*clips])
run('rom_extract.py',[f'{role}={ROOT}/anim_library/humanoid_set/{st}.glb:{clip}'for role,(st,clip)in roles.items()])
(P/'source/clip_candidates.json').write_text(json.dumps(roles,indent=2))
