"""Frame and half-frame cloth gate plus complete fall framing."""
import bpy,sys,json,numpy as np,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/skirt_animated.blend'))
r=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data;sc=bpy.context.scene
pv=np.array([x.value for x in me.attributes['piece'].data]);R=np.array([v.co[:] for v in me.vertices])
ids=np.flatnonzero(pv==100);E=np.array([list(e.vertices) for e in me.edges if all(pv[i]==100 for i in e.vertices)])
rl=np.linalg.norm(R[E[:,0]]-R[E[:,1]],axis=1)
report={};common.workbench_clay(sc)
for name in ('Standing','Walking','Hit','Death','Fidget'):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 f0,f1=map(int,a.frame_range);samps=[];maxstretch=(0,0);maxopening=(0,0);floor=(9,0)
 for f in np.arange(f0,f1+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1))
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();P=np.array([v.co[:] for v in mm.vertices]);ev.to_mesh_clear()
  length=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1);ratio=length/np.maximum(rl,1e-6);op=np.where(ratio>2,length-rl,0)
  v=float(np.percentile(ratio,99))
  if v>maxstretch[0]:maxstretch=(v,float(f))
  if op.max()>maxopening[0]:maxopening=(float(op.max()),float(f))
  if P[ids,2].min()<floor[0]:floor=(float(P[ids,2].min()),float(f))
  if f%1==0:samps.append(P[ids])
 P=np.array(samps);acc=np.linalg.norm(P[2:]-2*P[1:-1]+P[:-2],axis=2)
 report[name]={'edge_stretch_p99':maxstretch,'edge_opening_over_2x_m':maxopening,'min_cloth_z':floor,'jerk_p95_cm':float(np.percentile(acc,95)*100),'jerk_max_cm':float(acc.max()*100),'loop_seam_max_mm':float(np.linalg.norm(P[-1]-P[0],axis=1).max()*1000) if name in ('Standing','Walking','Fidget') else None}
 if name=='Death':
  for f in (f1//2,3*f1//4,f1):
   sc.frame_set(f);lo,hi=common.world_bounds([ob]);center=(lo+hi)*.5;extent=max(hi-lo)
   common.render_views(str(p/f'review/fall_full_{f}'),center.z,extent*1.35,views=('front','left','three_quarter'),resolution=(900,700),target=(center.x,center.y))
 print('CLOTH GATE',name,report[name])
(p/'work/skirt_gate.json').write_text(json.dumps(report,indent=2))
