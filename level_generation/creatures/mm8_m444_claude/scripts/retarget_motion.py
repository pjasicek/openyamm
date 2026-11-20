from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]; root=p.parents[2]; lib=root/'anim_library'
def run(name,args):
 sys.argv=[str(p/'scripts'/name),'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('retarget.py',[p/'work/rig_v1.blend',p/'work/rig_v2s.blend',f'{lib}/humanoid_set/Armed.glb:ArmedIdle:GripRef',f'{lib}/humanoid_set/Unarmed.glb:UnarmedGetHitF1:Hit',f'{lib}/humanoid_set/Armed.glb:ArmedCastLAttack1:Cast'])
run('retarget_mixamo.py',[p/'work/rig_v2s.blend',p/'work/rig_v2.blend']+[f'{lib}/mixamo/{src}.fbx:{role}' for src,role in [('Standard Idle','Standing'),('Walk','Walking'),('Standard Run','Running'),('Sword And Shield Slash','Attack:plant'),('Sword And Shield Slash','AttackFull:turn'),('Standing React Death Backward','Death'),('Standing Taunt Battlecry','Fidget:plant'),('Standing Taunt Battlecry','FidgetFull:turn')]])
