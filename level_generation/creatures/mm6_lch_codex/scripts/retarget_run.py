import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
src=str(P/'work/rig_v1.blend');out=str(P/'work/rig_animated_raw.blend')
groups=[('',[
 'Relax:RelaxIdle:Standing','Relax:RelaxWalkForward:Walking','Relax:RelaxDrink1:Fidget',
 'Unarmed:UnarmedDeath1:Death','Unarmed:UnarmedCastDualAttack2:AttackFull',
 'Unarmed:UnarmedCastDualAttack1:CastFull']),('Standing',[
 'Unarmed:UnarmedCastDualAttack2:Attack','Unarmed:UnarmedCastDualAttack1:Cast','Unarmed:UnarmedGetHitF1:Hit'])]
for plant,items in groups:
 os.environ['PLANT_FROM']=plant
 args=[f'anim_library/humanoid_set/{a.split(":")[0]}.glb:'+':'.join(a.split(':')[1:]) for a in items]
 sys.argv=['retarget.py','--',src,out,*args]
 runpy.run_path(str(P/'scripts/retarget.py'),run_name='__main__');src=out
os.environ['FINGER_K']='0.15';sys.argv=['fingers_relax.py','--',out,str(P/'work/rig_animated.blend')]
runpy.run_path(str(P/'scripts/fingers_relax.py'),run_name='__main__')
