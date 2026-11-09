import bpy,json,math,sys,os,runpy,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['BowAsset'];sc=bpy.context.scene;report={}
def posed(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=[o.matrix_world@x.co for x in m.vertices];ev.to_mesh_clear();return v
names={g.index:g.name for g in body.vertex_groups};keep=[]
for v in body.data.vertices:
 # Gripping left fingers and the pulling right fingers are checked separately with the release closeups.
 own=sum(g.weight for g in v.groups if 'Hand'in names[g.group]or'Finger'in names[g.group])>.5;keep.append(not own)
faces=[tuple(f.vertices)for f in body.data.polygons if all(keep[i]for i in f.vertices)]
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];worst=(0,0,None);floor=(99,0);pel=[];lean=[];headclear=0
 for tick in range(int(a.frame_range[1])*4+1):
  f=tick/4
  sc.frame_set(int(f),subframe=f-int(f));p=posed(body);q=posed(prop);tree=BVHTree.FromPolygons(p,faces)
  for i,v in enumerate(q):
   if prop.data.vertices[i].groups[0].group==prop.vertex_groups['Arrow'].index and (a.name not in ('Attack','Cast') or r.pose.bones['Arrow'].scale.x<.01):continue
   loc,normal,idx,dist=tree.find_nearest(v,.05)
   if loc is not None and dist>worst[0]and(v-loc).dot(normal)<-.7*dist:
    # Open shoulder flaps and the quiver lip are not solid half-spaces.
    inside=0
    for direction in [(1,.371,.123),(-1,.217,.623),(.137,1,.341),(.539,-1,.269)]:
     direction=Vector(direction).normalized();start=v.copy();hits=0
     for k in range(30):
      hit,n,face,distance=tree.ray_cast(start,direction)
      if hit is None:break
      hits+=1;start=hit+direction*.00001
     inside+=hits%2
    if inside>=3:worst=(dist,f,i)
  z=min(v.z for v in p+q)
  if z<floor[0]:floor=(z,f)
  pelvis=r.pose.bones['B_Pelvis'].head;d=r.pose.bones['B_Neck'].head-r.pose.bones['B_Spine'].head;pel.append(pelvis.z);lean.append(math.degrees(math.atan2(math.hypot(d.x,d.y),d.z)))
 report[a.name]={'contact_method':'nearest signed distance confirmed by 3 of 4 ray-parity directions','equipment_contact_cm':worst[0]*100,'contact_frame':worst[1],'contact_vertex':worst[2],'floor_min_cm':floor[0]*100,'floor_frame':floor[1],'pelvis_range_m':[min(pel),max(pel)],'trunk_lean_degrees':[min(lean),max(lean)]};print('EQUIPMENT',a.name,report[a.name])
(P/'work/equipment_gate.json').write_text(json.dumps(report,indent=2))
acts=[a.name for a in bpy.data.actions];picks=[f'{a.name}:{f}'for a in bpy.data.actions for f in range(int(a.frame_range[1])+1)]
def run(n,args):sys.argv=[n,'--',*args];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('g4_weights.py',['work/rig_equipped.blend','equipped',*picks]);run('g5_hand_stretch.py',['work/rig_equipped.blend',*acts]);run('g6_contacts.py',['work/rig_equipped.blend',*acts])
