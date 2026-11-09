"""Half-frame collar/armour contact and final strike timing on the equipped retained rig."""
import bpy,os,sys,json
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/male/runtime_ragged.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Kept'];scene=bpy.context.scene
D=np.load(P/'texturing/kept_m_uv.npz');faces=D['faces'];pc=D['piece'];parts={p:faces[pc==p].tolist() for p in (0,1,3,4)};report={'half_frame_step':.5,'clips':{},'impact':{}}
def evaluated(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pts=[o.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return pts
def samples(o):
 pts=evaluated(o);return pts+[(pts[e.vertices[0]]+pts[e.vertices[1]])*.5 for e in o.data.edges]+[sum((pts[i] for i in f.vertices),Vector())/len(f.vertices) for f in o.data.polygons]
def inside(tree,p):
 direction=Vector((.719,.371,.588)).normalized();origin=p.copy();hits=0
 for _ in range(64):
  hit,n,ix,d=tree.ray_cast(origin,direction,10.)
  if hit is None:return hits%2==1
  hits+=1;origin=hit+direction*1e-5
 raise AssertionError('ray')
for act in sorted(bpy.data.actions,key=lambda a:a.name):
 if not act.name.startswith('Kept_'):continue
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];row={};times=[];strikes=[]
 for f in np.arange(act.frame_range[0],act.frame_range[1]+.01,.5):
  scene.frame_set(int(f),subframe=float(f%1));points=evaluated(body);trees={p:BVHTree.FromPolygons(points,fs,all_triangles=True) for p,fs in parts.items()}
  for name in ['collar']+(['plate'] if 'Armed' in act.name or 'Mace' in act.name else []):
   obj=bpy.data.objects['hes_kept_'+name];depth=0.;which=None
   for pt in samples(obj):
    for part,tree in trees.items():
     hit,n,idx,dist=tree.find_nearest(pt,.025)
     if hit is not None and part!=0 and (pt-hit).dot(n)<-.5*dist and dist>depth and inside(tree,pt):depth=float(dist);which=part
   if depth>row.get(name,{}).get('depth_m',0):row[name]={'depth_m':depth,'part':which,'frame':float(f)}
  if act.name in ('Kept_MaceAttack','Kept_Attack'):
   times.append(float((f-act.frame_range[0])/30))
   if act.name=='Kept_MaceAttack':
    p=evaluated(bpy.data.objects['hes_kept_club']);strikes.append(-min(v.y for v in p))
   else:strikes.append(-rig.pose.bones['B_R_Finger2'].head.y)
 # Intended fast forward reach; first 95% of forward excursion is the contact frame.
 if times:
  s=np.array(strikes);threshold=s.min()+.95*(s.max()-s.min());i=int(np.where(s>=threshold)[0][0]);report['impact'][act.name]={'seconds':times[i],'frame':float(act.frame_range[0]+times[i]*30),'criterion':'first 95% of final equipped forward strike excursion','forward_m':float(s[i])}
 report['clips'][act.name]=row;print('PROP_GATE',act.name,row,flush=True)
report['pass']=all(all(v['depth_m']<.0001 for v in row.values()) for row in report['clips'].values())
(P/'review/attachment_contacts.json').write_text(json.dumps(report,indent=2)+'\n');print('IMPACT',report['impact'],'PASS',report['pass'],flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
