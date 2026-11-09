import bpy,json,math,sys,runpy
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/verify_export.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];s=bpy.context.scene;me=body.data
piece=np.array([v.value for v in me.attributes['piece'].data]);reports={};walk={}
def points():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();return co
for name in ['Standing','Walking','Hit','Fidget','Death','Dead']:
 a=bpy.data.actions[name];rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];end=int(a.frame_range[1]);floor=1e6;top=[];feet=[]
 for f in np.arange(0,end+.01,.5):
  s.frame_set(int(f),subframe=f%1);co=points();assert np.isfinite(co).all();floor=min(floor,float(co[:,2].min()));top.append(float(co[:,2].max()))
  if name=='Walking':feet.append([[float(np.mean(co[piece==p,1])),float(np.min(co[piece==p,2]))] for p in [6,7]])
 assert floor>-.005,(name,floor)
 reports[name]={'samples':2*end+1,'minimum_floor_m':floor,'maximum_height_m':max(top)}
 if name=='Walking':
  feet=np.array(feet);dy=np.diff(feet[:,:,0],axis=0)*60;ground=(feet[:-1,:,1]<.025)&(feet[1:,:,1]<.025)&(dy>0)
  speed=float(np.median(dy[ground]));walk={'planted_foot_speed_mps':speed,'stride_m':speed*end/30,'grounded_samples':int(ground.sum())}
assert .8<walk['stride_m']<2,walk
(P/'work/final_floor_stride.json').write_text(json.dumps({'clips':reports,'walk':walk},indent=2));print('FLOOR_STRIDE',reports,walk,flush=True)
info=json.loads((P/'export/export_info.json').read_text());info['walk_stride_m']=walk['stride_m'];(P/'export/export_info.json').write_text(json.dumps(info,indent=2))
for script,args in [('g4_weights.py',[str(P/'work/textured_uv.blend'),'final','Standing:0','Walking:8','Walking:24','Hit:4','Death:20','Fidget:48']),('g5_hand_stretch.py',[str(P/'work/textured_uv.blend'),'Standing','Walking','Hit','Fidget','Death']),('g6_contacts.py',[str(P/'work/textured_uv.blend'),'Standing','Walking','Hit','Fidget','Death'])]:
 sys.argv=[script,'--',*args];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
