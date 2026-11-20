"""Close the waist, fit the existing wrap and ground interpolated motion."""
import bpy,bmesh,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/posed.blend'))
r=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data;sc=bpy.context.scene
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();pv=[a.value for a in me.attributes['piece'].data];gn=[g.name for g in ob.vertex_groups]
report={'waist_extended_vertices':0,'tunic_overlap_vertices':0}
for v in me.vertices:
 z=v.co.z
 if pv[v.index]==1 and z>.96:
  t=min(1,(z-.96)/.05);v.co.z+=.14*t
  for g in ob.vertex_groups:g.remove([v.index])
  ob.vertex_groups['B_Pelvis'].add([v.index],1-.6*t,'REPLACE');ob.vertex_groups['B_Spine'].add([v.index],.6*t,'REPLACE');report['waist_extended_vertices']+=1
 if pv[v.index]==2 and z<1.14:
  t=max(0,min(1,(1.14-z)/.09));v.co.z-=.065*t
  weights={g.group:g.weight*(1-.65*t)for g in v.groups}
  weights[ob.vertex_groups['B_Pelvis'].index]=weights.get(ob.vertex_groups['B_Pelvis'].index,0)+.65*t
  for gi,w in weights.items():ob.vertex_groups[gi].add([v.index],w,'REPLACE')
  report['tunic_overlap_vertices']+=1
 # Wrist skin follows the hand; tiny inherited forearm weights caused the closed grip to breathe.
 if pv[v.index]==3:
  keep={g.group:g.weight for g in v.groups if gn[g.group]=='B_L_Hand'or gn[g.group].startswith('B_L_Finger')}
  if sum(keep.values())>.80:
   for g in ob.vertex_groups:g.remove([v.index])
   total=sum(keep.values())
   for gi,w in keep.items():ob.vertex_groups[gi].add([v.index],w/total,'REPLACE')
bm=bmesh.new();bm.from_mesh(me);piece=bm.verts.layers.int['piece'];vs=[v for v in bm.verts if v[piece]==1];bmesh.ops.remove_doubles(bm,verts=vs,dist=1e-6)
edges=[e for e in bm.edges if e.is_boundary and all(v[piece]==1 and v.co.z>1.07 for v in e.verts)]
new=bmesh.ops.holes_fill(bm,edges=edges,sides=0)['faces'];report['waist_cap_faces']=len(new)
for f in new:
 f.material_index=0
 for layer in bm.loops.layers.uv.values():
  for loop in f.loops:loop[layer].uv=(.5,.5)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
# Fit hand contact in the authored standing pose, then map the small correction back through its skin matrix.
a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
pv=np.array([a.value for a in me.attributes['piece'].data]);me.calc_loop_triangles();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();xyz=[v.co.copy()for v in m.vertices];ev.to_mesh_clear()
inv=r.data.bones['Bow'].matrix_local.inverted();wrap=[list(f.vertices)for f in me.loop_triangles if all(pv[i]==201 and abs((inv@me.vertices[i].co).z)<.105 for i in f.vertices)]
tree=BVHTree.FromPolygons(xyz,wrap);mats={g.index:np.array(r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted())for g in ob.vertex_groups if g.name in r.pose.bones}
changed=0
for v in me.vertices:
 if pv[v.index]!=3:continue
 hand=sum(g.weight for g in v.groups if gn[g.group]=='B_L_Hand'or gn[g.group].startswith('B_L_Finger'))
 if hand<.8:continue
 hit,n,_,dist=tree.find_nearest(xyz[v.index]);delta=Vector()
 if dist<.014 and (xyz[v.index]-hit).dot(n)<0:delta=hit+n*.001-xyz[v.index]
 # The outer claw was 0.6 mm short of contact after the previous simplification.
 pinky=sum(g.weight for g in v.groups if gn[g.group].startswith('B_L_Finger4'))
 if pinky>.4 and dist<.009 and not delta.length:delta=(hit-xyz[v.index]).normalized()*.0018
 if delta.length:
  skin=sum((mats[g.group]*g.weight for g in v.groups if g.group in mats),np.zeros((4,4)))
  v.co=Vector((np.linalg.inv(skin)@np.r_[np.array(xyz[v.index]+delta),1])[:3]);changed+=1
report['grip_fitted_vertices']=changed;me.update()
# Ground the actual deformed surface, including the bow, at quarter frames.
root=r.pose.bones['B_Pelvis'];rootinv=r.data.bones[root.name].matrix_local.to_3x3().inverted();report['floor']={}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];N=int(a.frame_range[1]);loc=[];correction=np.zeros(N+1)
 for f in range(N+1):sc.frame_set(f);loc.append(root.location.copy())
 for tick in range(N*4+1):
  f=tick/4;sc.frame_set(int(f),subframe=f%1);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();low=min(v.co.z for v in m.vertices if pv[v.index]!=202);ev.to_mesh_clear();dz=max(0,.001-low)
  for i in {int(f),min(N,math.ceil(f))}:correction[i]=max(correction[i],dz)
 for f,l in enumerate(loc):root.location=l+rootinv@Vector((0,0,float(correction[f])));root.keyframe_insert('location',frame=f)
 if a.name in ['Death','Dead']:
  for f in range(N+1):
   if a.name=='Death'and f<=30:continue
   sc.frame_set(f);bone=r.pose.bones['Bow'];m=bone.matrix.copy();w=1 if a.name=='Dead'else max(0,min(1,(f-30)/2));m.translation.z-=float(correction[f])*w;bone.matrix=m
   for channel in ['rotation_quaternion','location','scale']:bone.keyframe_insert(channel,frame=f)
 report['floor'][a.name]=float(max(correction))
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round4/repaired.blend'))
(P/'review/round4/repairs.json').write_text(json.dumps(report,indent=2));print('REPAIRS',report,flush=True)
