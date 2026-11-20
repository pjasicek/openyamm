import bpy,numpy as np,sys,json
from pathlib import Path
from mathutils import Vector,kdtree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data;r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
pv=np.array([x.value for x in me.attributes['piece'].data]);report={}
for sd,part,opening in [('L',2,.093),('R',3,.066)]:
 el=r.data.bones[f'B_{sd}_Forearm'].head_local;axis=(r.data.bones[f'B_{sd}_Hand'].head_local-el).normalized();changes=[]
 for v in me.vertices:
  if pv[v.index]!=part:continue
  t=(v.co-el).dot(axis);fade=min(1,max(0,(t-opening)/.045));factor=.55+.45*fade
  if factor<1:
   center=el+axis*t;before=v.co.copy();v.co=center+(v.co-center)*factor;changes.append((v.co-before).length)
 report[sd]={'hidden_root_vertices_tucked':len(changes),'max_move_mm':max(changes)*1000}
# Coat tails follow their adjacent trouser surface, preventing the two layers from shearing through each other.
ids=[v.index for v in me.vertices if pv[v.index]==1];tree=kdtree.KDTree(len(ids))
for i in ids:tree.insert(me.vertices[i].co,i)
tree.balance();changed=0
for v in me.vertices:
 if pv[v.index]==0 and v.co.z<1.08 and abs(v.co.x)<.26:
  _,i,d=tree.find(v.co);blend=min(1,max(0,(1.08-v.co.z)/.08));old={g.group:g.weight for g in v.groups};src={g.group:g.weight for g in me.vertices[i].groups};merged={k:old.get(k,0)*(1-blend)+src.get(k,0)*blend for k in old.keys()|src.keys()}
  for g in list(v.groups):b.vertex_groups[g.group].remove([v.index])
  for k,w in merged.items():
   if w>.00001:b.vertex_groups[k].add([v.index],w,'REPLACE')
  changed+=1
for v in me.vertices:
 if pv[v.index]==1 and v.co.z>.79:
  f=1-.075*min(1,(v.co.z-.79)/.05);center=Vector((.10 if v.co.x>0 else -.10,0,v.co.z));v.co=center+(v.co-center)*f
bpy.context.view_layer.objects.active=b;b.select_set(True);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False);me.update();bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured.blend'));report['coat_vertices_matched']=changed;(p/'review/cloth_fit.json').write_text(json.dumps(report,indent=2))
