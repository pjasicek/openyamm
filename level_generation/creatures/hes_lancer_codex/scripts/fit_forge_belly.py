"""Fit the middle belly lamella across the complete pose set, with explicit rigid-piece clearance."""
import bpy,sys,os,runpy,json,itertools
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];S=P/'scripts';src=P/'work/forge_apron.blend';out=P/'work/forge_final_fit.blend'
sys.argv=['armour_gate.py','--',str(src),'forge_belly_masks',str(S/'armour_forge.json')];g=runpy.run_path(str(S/'armour_gate.py'),run_name='__main__');r=g['rig'];sc=bpy.context.scene;name='Arm_abdomen_upper';ob=bpy.data.objects[name];rest=g['REST_P'][name];frames=[];neighbors=['Arm_abdomen_u','Arm_chest','Apron_Chest','Arm_belt']
clips=['Forge_'+x for x in ('Death','Running','Cast','Attack','Standing','Walking','Hit','Fidget','Dead')]
for clip in [None,*clips]:
 if clip is None:
  r.animation_data.action=None
  for b in r.pose.bones:b.matrix_basis.identity()
  ticks=[0]
 else:
  a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];ticks=range(int(a.frame_range[0]),int(a.frame_range[1])+1)
 for f in ticks:
  sc.frame_set(f);bpy.context.view_layer.update();body,_=g['ev'](g['body']);others={n:g['ev'](bpy.data.objects[n])[0] for n in neighbors}
  matrices={n:np.array(r.pose.bones[n].matrix@r.data.bones[n].matrix_local.inverted()) for n in ('B_Spine1','B_Spine2','B_Spine')}
  frames.append((clip,f,body,BVHTree.FromPolygons(body.tolist(),g['BFK']),others,{n:BVHTree.FromPolygons(v.tolist(),g['pfaces'][n]) for n,v in others.items()},matrices))
 print('BELLY_POSES',clip,len(frames),flush=True)
shifts=sorted(itertools.product((-.04,-.02,0,.02,.04),repeat=2),key=lambda x:x[0]**2+x[1]**2)
rows=[];chosen=None
for bone in ('B_Spine1','B_Spine2','B_Spine'):
 for dy,dz in shifts:
  moved=rest+np.array([0,dy,dz]);worst=0;failure=None
  for clip,f,body,bt,others,trees,matrices in frames:
   m=matrices[bone];pp=moved@m[:3,:3].T+m[:3,3];lo,hi=pp.min(0),pp.max(0);pt=BVHTree.FromPolygons(pp.tolist(),g['pfaces'][name]);dep=g['inside_closed'](bt,pp[g['PV'][name]],1.2,g['HIDFK'])[0]
   candidates=np.where((g['HID']==0)&np.all((body>lo-.005)&(body<hi+.005),axis=1))[0]
   if len(candidates):dep=max(dep,g['inside_closed'](pt,body[candidates])[0])
   for n,other in others.items():
    if np.any(lo>other.max(0)) or np.any(hi<other.min(0)):continue
    dep=max(dep,g['inside_closed'](trees[n],pp[g['PV'][name]])[0],g['inside_closed'](pt,other[g['PV'][n]])[0])
   worst=max(worst,dep)
   if dep>.0025:failure=[clip,f,dep];break
  row=dict(bone=bone,dy=dy,dz=dz,worst=worst,failure=failure);rows.append(row)
  if failure is None:chosen=row;break
 if chosen:break
print('BELLY_RESULT',chosen,'tried',len(rows),flush=True);(P/'review/forge_belly_fit.json').write_text(json.dumps({'chosen':chosen,'candidates':rows},indent=2)+'\n');assert chosen,rows
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
for v in ob.data.vertices:v.co.y+=chosen['dy'];v.co.z+=chosen['dz']
spec=json.loads((S/'armour_forge.json').read_text())
for plate in spec['plates']:
 if plate['name']=='abdomen_upper':plate['bone']=chosen['bone'];plate['shell']['bones']=[chosen['bone']]
ob['bone']=chosen['bone'];(S/'armour_forge.json').write_text(json.dumps(spec,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(out))
sys.argv=['skin_shell.py','--',str(out),str(S/'armour_forge.json'),str(out)];runpy.run_path(str(S/'skin_shell.py'),run_name='__main__')
sys.argv=['armour_gate.py','--',str(out),'forge_belly',str(S/'armour_forge.json'),*clips];runpy.run_path(str(S/'armour_gate.py'),run_name='__main__')
sys.stdout.flush();os._exit(0)
