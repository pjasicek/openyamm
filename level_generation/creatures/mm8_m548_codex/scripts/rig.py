"""Fit the local crystal-dragon rig to measured geometry; keep crown/toes rigid."""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_v1.blend'))
m=bpy.data.objects['CrystalDragon']
# Shorten only the free tail, preserving its crystal tip and the torso junction.
for v in m.data.vertices:
    if v.co.y>.23 and v.co.z>.25:
        v.co.y=.23+(v.co.y-.23)*.65
chains={
 'Spine':(None,[(0,.09,.34),(0,-.07,.35),(0,-.23,.39),(0,-.30,.46)],['Spine1','Spine2','Spine3']),
 'Neck':('Spine3',[(0,-.30,.46),(0,-.34,.56),(0,-.35,.65)],['Neck1','Neck2']),
 'Head':('Neck2',[(0,-.35,.65),(0,-.47,.67)],['Head']),
 'Jaw':('Head',[(0,-.375,.65),(0,-.48,.635)],['Jaw']),
 'Tail':('Spine1',[(0,.16,.34),(0,.29,.34),(0,.40,.36)],['Tail1','Tail2'])}
for side,s in [('L',1),('R',-1)]:
 chains['Front'+side]=('Spine3',[(s*.12,-.28,.39),(s*.13,-.245,.22),(s*.15,-.31,.055),(s*.17,-.41,.02)],['UpperArm_'+side,'ForeArm_'+side,'FrontPaw_'+side])
 chains['Hind'+side]=('Spine1',[(s*.13,.10,.345),(s*.15,.065,.235),(s*.17,.215,.13),(s*.19,.18,.05),(s*.20,.08,.02)],['Thigh_'+side,'Shin_'+side,'Tarsus_'+side,'HindPaw_'+side])
arm=bpy.data.armatures.new('CrystalDragonRig');rig=bpy.data.objects.new('CrystalDragonRig',arm);bpy.context.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for key,(parent,pts,names) in chains.items():
 prev=arm.edit_bones.get(parent) if parent else None
 for i,n in enumerate(names):
  b=arm.edit_bones.new(n);b.head=pts[i];b.tail=pts[i+1];b.parent=prev;b.use_connect=i>0
  b.align_roll(Vector((0,-1,0)) if key.startswith(('Front','Hind')) else Vector((0,0,1)));prev=b
bpy.ops.object.mode_set(mode='OBJECT')
# Own each limb before blending weights: nearby belly and opposite limbs stay on the trunk.
import numpy as np
names=[b.name for b in arm.bones]
for n in names:m.vertex_groups.new(name=n)
verts=np.array([tuple(v.co) for v in m.data.vertices]);weights=np.zeros((len(verts),len(names)))
body_names=['Spine1','Spine2','Spine3','Neck1','Neck2','Head','Tail1','Tail2']
for i,v in enumerate(verts):
 x,y,z=v;side='L' if x>0 else 'R'
 if z<.29 and abs(x)>.065:
  allowed=([f'{n}_{side}' for n in ['UpperArm','ForeArm','FrontPaw']] if y<-.14 else [f'{n}_{side}' for n in ['Thigh','Shin','Tarsus','HindPaw']])
  if z>.23:allowed+=['Spine1','Spine2','Spine3']
 elif z>.615:allowed=['Head']
 elif y>.235 and z>.25:allowed=['Tail1','Tail2']
 else:allowed=body_names+[f'{n}_{side}' for n in ['Thigh','UpperArm']]
 for n in allowed:
  bone=arm.bones[n];h=np.array(bone.head_local);delta=np.array(bone.tail_local)-h
  t=np.clip(np.dot(v-h,delta)/np.dot(delta,delta),0,1);distance=np.linalg.norm(v-(h+t*delta))
  weights[i,names.index(n)]=1/(distance+.012)**4
 weights[i]/=weights[i].sum()
edges=np.array([tuple(e.vertices) for e in m.data.edges]);degree=np.bincount(edges.ravel(),minlength=len(verts))
for _ in range(5):
 avg=np.zeros_like(weights)
 np.add.at(avg,edges[:,0],weights[edges[:,1]]);np.add.at(avg,edges[:,1],weights[edges[:,0]])
 weights=.65*weights+.35*avg/np.maximum(degree[:,None],1)
 weights/=weights.sum(axis=1,keepdims=True)
for i,w in enumerate(weights):
 keep=np.argsort(w)[-4:];total=w[keep].sum()
 for j in keep:
  if w[j]>1e-7:m.vertex_groups[names[j]].add([i],float(w[j]/total),'REPLACE')
mod=m.modifiers.new('Armature','ARMATURE');mod.object=rig;m.parent=rig
assert all(v.groups for v in m.data.vertices),'Region weights incomplete'
def rigid(v,n):
 for g in list(v.groups):m.vertex_groups[g.group].remove([v.index])
 m.vertex_groups[n].add([v.index],1,'REPLACE')
for v in m.data.vertices:
 x,y,z=v.co;side='L' if x>0 else 'R'
 if z>.635:
  rigid(v,'Head')
 elif y<-.405 and z>.615:
  rigid(v,'Jaw')
 elif z<.052:
  rigid(v,('FrontPaw_' if y<-.15 else 'HindPaw_')+side)
# Small disconnected crystal pieces must move with their nearest main surface.
adj=[set() for _ in m.data.vertices]
for e in m.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();parts=[]
for i in range(len(adj)):
 if i in seen:continue
 part=[];stack=[i];seen.add(i)
 while stack:
  k=stack.pop();part.append(k)
  for j in adj[k]-seen:seen.add(j);stack.append(j)
 parts.append(part)
parts.sort(key=len,reverse=True)
from mathutils.kdtree import KDTree
kd=KDTree(len(parts[0]))
for i in parts[0]:kd.insert(m.data.vertices[i].co,i)
kd.balance()
part_info=[]
for part in parts:
 center=sum((m.data.vertices[i].co for i in part),Vector())/len(part)
 totals={}
 for i in part:
  for g in m.data.vertices[i].groups:
   n=m.vertex_groups[g.group].name;totals[n]=totals.get(n,0)+g.weight
 dominant=max(totals,key=totals.get)
 part_info.append({'vertices':len(part),'center':list(center),'dominant':dominant,'dominant_share':totals[dominant]/len(part)})
 if part is parts[0]:continue
 if totals[dominant]/len(part)>.90:
  for i in part:rigid(m.data.vertices[i],dominant)
 elif len(part)<50:
  _,near,_=kd.find(center);groups=list(m.data.vertices[near].groups)
  name=m.vertex_groups[max(groups,key=lambda g:g.weight).group].name
  for i in part:rigid(m.data.vertices[i],name)
(P/'work/component_weights.json').write_text(json.dumps(part_info,indent=2))
bpy.context.view_layer.objects.active=m
bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in m.data.vertices)
# The attack release follows the head, at the mouth opening.
socket=bpy.data.objects.new('Socket_Mouth',None);bpy.context.collection.objects.link(socket)
socket.parent=rig;socket.parent_type='BONE';socket.parent_bone='Head'
bpy.context.view_layer.update();socket.matrix_world.translation=Vector((0,-.488,.647))
rig.show_in_front=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
(P/'work/rig_info.json').write_text(json.dumps({'bones':len(arm.bones),'components':[len(c) for c in parts],'joints':chains,'unweighted':0,'max_influences':max(len(v.groups) for v in m.data.vertices)},indent=2))
print('RIG_OK',len(arm.bones),[len(c) for c in parts],flush=True)
