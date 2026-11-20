from pathlib import Path
import bpy,sys,json,numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path('anim_library/humanoid_set/Unarmed.glb').resolve()))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');act=next(a for a in bpy.data.actions if a.name.split('|')[-1].split('@')[-1]=='UnarmedIdle');rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(0)
def circle(P):
 c=P.mean(0);u=np.linalg.svd(P-c)[2];xy=np.c_[(P-c)@u[0],(P-c)@u[1]];sol=np.linalg.lstsq(np.c_[2*xy,np.ones(len(P))],(xy*xy).sum(1),rcond=None)[0];return c+sol[0]*u[0]+sol[1]*u[1]
out={}
for s in 'LR':
 H=rig.matrix_world@rig.pose.bones[f'B_{s}_Hand'].matrix;centres=[];kn=[]
 for i in (1,2,3,4):
  pts=np.array([(rig.matrix_world@rig.pose.bones[n].head)[:] for n in (f'B_{s}_Finger{i}',f'B_{s}_Finger{i}1',f'B_{s}_Finger{i}2')]);centres.append(circle(pts));kn.append(pts[0])
 centres=np.array(centres);kn=np.array(kn);A=np.linalg.svd(centres-centres.mean(0))[2][0]
 if A@(kn[0]-kn[-1])<0:A=-A
 f=kn.mean(0)-np.array(H.translation);f/=np.linalg.norm(f);n=np.cross(A,f);n/=np.linalg.norm(n)
 if n@(centres.mean(0)-kn.mean(0))<0:n=-n
 out[s]={'source':'Unarmed.glb:UnarmedIdle:0','axis_hand':list(H.to_3x3().inverted()@Vector(A)),'palm_normal_hand':list(H.to_3x3().inverted()@Vector(n))}
(p/'work/source_fist.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
