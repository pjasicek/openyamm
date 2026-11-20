"""Fit existing vertices to the mount/grip; preserve every polygon and UV."""
import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sel=json.loads((P/'review/round2/before/reduction_selected.json').read_text());out=P/'work/round2_contact';out.mkdir(exist_ok=True);report={}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/final_lod{level}.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];blade=bpy.data.objects['ForearmBlade'];shield=bpy.data.objects['LeafShield'];sc=bpy.context.scene;counts={o.name:sum(len(f.vertices)-2 for f in o.data.polygons)for o in [body,blade,shield]}
 a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0);bpy.context.view_layer.update();me=body.data;gn={g.index:g.name for g in body.vertex_groups};S=rig.pose.bones['LeafShield'].matrix.copy();SI=S.inverted();localskin=[];before=np.array([tuple(v.co)for v in me.vertices]);groups=[]
 for v in me.vertices:
  mat=Matrix(((0,0,0,0),)*4)
  for g in v.groups:
   n=gn[g.group]
   if n in rig.data.bones:mat+=g.weight*(rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted())
  localskin.append(SI@mat)
  groups.append({gn[g.group]:g.weight for g in v.groups})
 ids=[v.index for v in me.vertices if sum(w for n,w in groups[v.index].items()if n.startswith('B_L_Hand')or n.startswith('B_L_Finger'))>.3]
 M=rig.data.bones['LeafShield'].matrix_local.inverted();vc=[M@v.co for v in shield.data.vertices];faces=[tuple(f.vertices)for f in shield.data.polygons if all(abs(vc[i].x)<.09 and abs(vc[i].y-.045)<.022 and abs(vc[i].z-.26)<.021 for i in f.vertices)];tree=BVHTree.FromPolygons(vc,faces);assert faces
 inv=[m.inverted_safe()for m in localskin]
 def local(i):return localskin[i]@me.vertices[i].co
 def move(i,q):me.vertices[i].co=inv[i]@q
 # Clear the actual bar volume, including the coarse facets at far LODs.
 for iteration in range(4):
  for i in ids:
   q=local(i);d=Vector((0,q.y-.045,q.z-.26));r=d.length
   if abs(q.x)<.076 and r<.0125:
    if r<1e-6:d=Vector((0,0,-1));r=1
    move(i,q+d*(.0125/r-1))
  # Contact on each digit and palm. A small neighbourhood moves with the closest vertex.
  for root in ['B_L_Hand']+[f'B_L_Finger{k}'for k in range(5)]:
   members=[i for i in ids if sum(w for n,w in groups[i].items()if n==root or (root!='B_L_Hand'and n.startswith(root)))>.3]
   hits=[tree.find_nearest(local(i))for i in members];j=min(range(len(members)),key=lambda j:hits[j][3]);hit,norm,_,dist=hits[j];i=members[j];q0=local(i)
   if dist<=.002:continue
   direction=(q0-hit).normalized();target=hit+direction*.0015;delta=target-q0
   for k in members:
    q=local(k);weight=np.exp(-((q-q0).length/.017)**2);move(k,q+delta*float(weight))
  me.update()
 after=np.array([tuple(v.co)for v in me.vertices]);report[str(level)]={'hand_max_vertex_shift_mm':float(np.linalg.norm(after-before,axis=1).max()*1000)}
 # The main blade's concave root was inside the forearm instead of seated above the cuffs.
 mb=rig.data.bones['ForearmBlade'].matrix_local;iv=mb.inverted();coords=[iv@v.co for v in blade.data.vertices];adj=[[]for _ in coords]
 for e in blade.data.edges:
  i,j=e.vertices;adj[i].append(j);adj[j].append(i)
 todo=set(range(len(coords)));components=[]
 while todo:
  seed=todo.pop();part=[seed]
  for i in part:
   for j in adj[i]:
    if j in todo:todo.remove(j);part.append(j)
  components.append(part)
 main=max(components,key=lambda ids:max(coords[i].z for i in ids)-min(coords[i].z for i in ids));assert max(coords[i].z for i in main)>.6
 for i in main:
  q=coords[i];t=max(0,min(1,q.z/.25));q.x+=.045*(1-t*t*(3-2*t));blade.data.vertices[i].co=mb@q
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();dest=out/f'lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest))
 for part in ['Body','ForearmBlade']:
  sel[part][str(level)]['blend']=str(dest.relative_to(P))
 assert counts=={o.name:sum(len(f.vertices)-2 for f in o.data.polygons)for o in [body,blade,shield]}
 report[str(level)]['triangles']=counts
(P/'review/reduction_selected.json').write_text(json.dumps(sel,indent=2));(P/'review/round2/contact_fitting.json').write_text(json.dumps(report,indent=2))
