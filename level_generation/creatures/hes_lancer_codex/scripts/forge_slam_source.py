import sys,os,runpy,json,math
from pathlib import Path
import bpy
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
choice=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'axeair'
sources={'mixamo':('bar1_retarget_mixamo.py','anim_library/mixamo/Standing Melee Attack Downward.fbx:Slam_Mixamo','Slam_Mixamo'),'axeair':('retarget.py','anim_library/humanoid_set/2Hand Axe.glb:2HandAxeAirAttack1:Slam_AxeAir','Slam_AxeAir'),'swordair':('retarget.py','anim_library/humanoid_set/2Hand Sword.glb:2HandSwordAirAttack1:Slam_SwordAir','Slam_SwordAir')}
script,item,action=sources[choice]
sys.argv=['retarget','--',str(P/'work/before_strike_20261024/work/forge_complete.blend'),str(P/f'work/forge_slam_source_{choice}.blend'),item]
runpy.run_path(str(P/'scripts'/script),run_name='__main__')
r=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions[action];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];axis=Vector(json.loads((P/'work/maul_source_grips.json').read_text())['R']['axis_hand']).normalized();rows=[]
for f in range(int(a.frame_range[1])+1):
 sc.frame_set(f);m=armik.W(r,'B_R_Hand');rows.append({'frame':f,'axis':list(m.to_3x3().normalized()@axis),'hands':{s:list(armik.W(r,f'B_{s}_Hand').translation) for s in 'LR'},'pelvis':list(armik.W(r,'B_Pelvis').translation)})
(P/f'review/forge_slam_{choice}_probe.json').write_text(json.dumps(rows,indent=2)+'\n');print('SOURCE_PROBE',choice,'frames',len(rows),flush=True);sys.stdout.flush();os._exit(0)
