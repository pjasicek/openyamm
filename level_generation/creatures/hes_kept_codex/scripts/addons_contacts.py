"""Measure all fitted add-ons, candidate strike paths and closed-skin contacts at half frames."""
import bpy,sys,os,json
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/addons_v2/equipped.blend'));r=bpy.data.objects['Rig'];body=bpy.data.objects['Kept'];sc=bpy.context.scene;fs=np.array([p.vertices[:] for p in body.data.polygons]);pc=np.array([body.data.attributes['piece'].data[p.vertices[0]].value for p in body.data.polygons]);report={}
def points(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();p=[o.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return p
triangles={}
def inside(tree,p):
 # A grazing ray can skip two skin crossings separated by <10 micrometres. Confirm candidates by solid angle.
 candidates=False
 for direction in ((.719,.371,.588),(1,.12,.3),(-.24,.91,.12)):
  v=Vector(direction).normalized();q=p.copy();hits=0
  for i in range(64):
   hit,n,ix,d=tree.ray_cast(q,v,10)
   if hit is None:break
   hits+=1;q=hit+v*.00001
  else:raise AssertionError('ray')
  candidates |= bool(hits%2)
 if not candidates:return False
 a,b,c=(triangles[id(tree)]-np.array(p,dtype=float)).transpose(1,0,2);la=np.linalg.norm(a,axis=1);lb=np.linalg.norm(b,axis=1);lc=np.linalg.norm(c,axis=1)
 num=np.einsum('ij,ij->i',a,np.cross(b,c));den=la*lb*lc+np.einsum('ij,ij->i',a,b)*lc+np.einsum('ij,ij->i',b,c)*la+np.einsum('ij,ij->i',c,a)*lb
 return abs(float(np.arctan2(num,den).sum()/(2*np.pi)))>.5
from collections import Counter
for part in (1,3,4):
 edges=Counter(tuple(sorted((f[i],f[(i+1)%3])))for f in fs[pc==part]for i in range(3));assert all(v==2 for v in edges.values()),(part,'skin is not closed')
for a in sorted(bpy.data.actions,key=lambda a:a.name):
 if not a.name.startswith('Kept_') or a.name in ('Kept_ClubR2','Kept_ClubSword1') or (os.environ.get('KEPT_CHECK_ACTION') and a.name!=os.environ['KEPT_CHECK_ACTION']):continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];props=['collar']+(['plate','club','pick'] if a.name.startswith('Kept_Armed') else ['plate','club'] if a.name.startswith('Kept_Club') else ['pick'] if a.name=='Kept_MaceAttack' else []);row={n:{'skin_depth_m':0.,'floor_m':1e9,'cloth_inward_proximity_m':0.} for n in props};path=[]
 for f in np.arange(0,a.frame_range[1]+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1));bpts=points(body);trees={part:BVHTree.FromPolygons(bpts,fs[pc==part].tolist(),all_triangles=True) for part in (0,1,3,4)}
  triangles={id(tree):np.array(bpts,dtype=float)[fs[pc==part]] for part,tree in trees.items()}
  for name in props:
   o=bpy.data.objects['hes_kept_'+name];ps=points(o);row[name]['floor_m']=min(row[name]['floor_m'],min(v.z for v in ps));samples=ps+[(ps[e.vertices[0]]+ps[e.vertices[1]])*.5 for e in o.data.edges]+[sum((ps[v] for v in p.vertices),Vector())/len(p.vertices) for p in o.data.polygons]
   if name in ('pick','club'):
    # Extremal forward point of the head, rather than the hand/haft.
    local=np.array([v.co[:] for v in o.data.vertices]);handle=r.data.bones['B_R_Hand'].head_local;hand=r.pose.bones['B_R_Hand'].head;far=[p for p in ps if (p-hand).length>.3];tip=min(far,key=lambda p:p.y);path.append([float(f),*map(float,tip)])
   for pt in samples:
    for part,tree in trees.items():
     hit,n,ix,dist=tree.find_nearest(pt,.05)
     if hit is None or dist<.0002 or (pt-hit).dot(n)>-.5*dist:continue
     if part==0:
      # Ignore far back surfaces of the open shirt; local inward samples need checking.
      if name=='plate' and dist<.015 and dist>row[name]['cloth_inward_proximity_m']:row[name].update(cloth_inward_proximity_m=float(dist),cloth_frame=float(f))
     elif inside(tree,pt) and dist>row[name]['skin_depth_m']:row[name].update(skin_depth_m=float(dist),skin_part=part,skin_frame=float(f))
 report[a.name]={'props':row,'weapon_tip_path':path};print('ADDON_CONTACT',a.name,row,flush=True)
(P/'review/addons_v2'/('contacts_'+os.environ['KEPT_CHECK_ACTION']+'.json' if os.environ.get('KEPT_CHECK_ACTION') else 'contact_probe.json')).write_text(json.dumps(report,indent=2)+'\n');
assert all(d['skin_depth_m']<.0001 for r in report.values()for d in r['props'].values()),[(a,p,d)for a,r in report.items()for p,d in r['props'].items()if d['skin_depth_m']>=.0001]
sys.stdout.flush();sys.stderr.flush();os._exit(0)
