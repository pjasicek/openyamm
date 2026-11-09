import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/production_master.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;report={}
for name in ['Attack','Cast']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];ts=np.arange(0,a.frame_range[1]/scene.render.fps+1e-6,1/240);xyz=[];normal=[]
 for t in ts:
  f=t*scene.render.fps;scene.frame_set(int(f),subframe=f-int(f));b=rig.pose.bones['Socket_Palm_Left'];xyz.append(list(rig.matrix_world@b.head));normal.append(list((rig.matrix_world@b.matrix).to_3x3()@Vector((0,1,0))))
 xyz=np.array(xyz);velocity=np.gradient(xyz,1/240,axis=0);valid=(ts>.6)&(ts<.9);score=np.where(valid,-velocity[:,1],-1e9);i=int(score.argmax())
 report[name]={'release_seconds':round(float(ts[i]),6),'forward_speed_mps':float(score[i]),'palm_position_m':xyz[i].tolist(),'palm_normal':normal[i],'palm_forward_dot':float(-normal[i][1]),'criterion':'Maximum forward palm-socket speed in the release gesture; staff is a focus, not a cutting blade.'}
 assert score[i]>.4
(p/'work/motion_details.json').write_text(json.dumps(report,indent=2));print('RELEASE',report)
