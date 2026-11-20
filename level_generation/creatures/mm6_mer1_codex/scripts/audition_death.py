import bpy,sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
files=['Falling Forward Death','Standing Death Forward 02','Standing Death Forward 01']
sys.argv=['retarget','--','work/actions_fingers.blend','work/death_audition.blend',*[str(R/'anim_library/mixamo'/f'{n}.fbx')+f':Death{i}'for i,n in enumerate(files)]];runpy.run_path(str(P/'scripts/retarget_mixamo.py'),run_name='__main__')
import common
r=bpy.data.objects['Rig'];s=bpy.context.scene;common.workbench_clay(s)
for j in range(3):
 a=bpy.data.actions[f'Death{j}'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for i in range(5):
  f=a.frame_range[1]*i/4;s.frame_set(int(f),subframe=f%1);common.render_views(str(P/'review'/f'death_audition_{j}_{i}'),.5,2.5,views=('left','three_quarter'),resolution=(360,450))
sys.argv=['grip','--','work/pilot.blend','GripRef','8'];os.environ['GRIP_RENDER']=str(P/'review/grip_v2');runpy.run_path(str(P/'scripts/grip_solve.py'),run_name='__main__')
