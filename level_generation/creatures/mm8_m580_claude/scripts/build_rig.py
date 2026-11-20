"""Fit the four-paddle Meshy return to native proportions and rigid-shell anatomy."""
from pathlib import Path
import bpy,bmesh,json,math
import numpy as np
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_v2.blend'))
m=bpy.data.objects['Turtle'];labels=np.load(P/'work/components_v2.npy');original=np.array([v.co[:] for v in m.data.vertices])
assert len(labels)==len(original)==7926
# Cut the soft neck cross-section in the graph; horns remain attached to their skull, not the nearby shell.
adj=[[] for _ in original]
for e in m.data.edges:
 a,b=e.vertices;p,q=original[a],original[b]
 if (p[1]+.255)*(q[1]+.255)<0 and max(p[2],q[2])<.305:continue
 adj[a].append(b);adj[b].append(a)
seed=int(np.argmin(original[:,1]+(labels!=1)*10));head=set([seed]);todo=[seed]
while todo:
 for j in adj[todo.pop()]:
  if j not in head:head.add(j);todo.append(j)
assert 800<len(head)<4500,len(head)
for k in range(7):m.vertex_groups.new(name=f'Part{k}').add(np.flatnonzero(labels==k).tolist(),1,'REPLACE')
m.vertex_groups.new(name='HeadSource').add(sorted(head),1,'REPLACE')
for v in m.data.vertices:
 p=original[v.index];k=labels[v.index]
 if v.index in head or k==6:v.co.y-=.20
 elif k==1 and p[1]<-.22 and abs(p[0])<.07 and p[2]<.27:v.co.y-=.20*float(np.clip((-.22-p[1])/.035,0,1))
 elif k in [0,5]:
  root=Vector((-.13 if k==0 else .13,.22,.22));v.co=root+(v.co-root)*.65
 elif k in [2,3]:
  sg=-1 if k==2 else 1;root=Vector((sg*.08,-.115,.24));v.co=root+Matrix.Rotation(math.radians(sg*45),3,'Z')@(v.co-root)
 elif k==4:v.co.y=.31+(v.co.y-.31)*2.9
# Resolve small accidental shell holes and inconsistent normals, preserving actual mouth boundaries.
bm=bmesh.new();bm.from_mesh(m.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
# Close measured shell defects and hidden flipper/tail roots; preserve the open tongue sheet.
remaining={e for e in bm.edges if e.is_boundary};deform=bm.verts.layers.deform.active
while remaining:
 todo=[remaining.pop()];edges=[]
 while todo:
  e=todo.pop();edges.append(e)
  for v in e.verts:
   for j in v.link_edges:
    if j in remaining:remaining.remove(j);todo.append(j)
 vs={v for e in edges for v in e.verts}
 if len(edges)<=8 or min(v.co.y for v in vs)>-.5:
  center=bm.verts.new(sum((v.co for v in vs),Vector())/len(vs))
  for group,value in next(iter(vs))[deform].items():center[deform][group]=value
  for e in edges:
   start=e.link_loops[0].vert;bm.faces.new((e.other_vert(start),start,center))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
print('BOUNDARIES',len([e for e in bm.edges if e.is_boundary]),'NONMANIFOLD',len([e for e in bm.edges if not e.is_manifold]),flush=True)
bm.to_mesh(m.data);bm.free()
owners=[]
for v in m.data.vertices:
 names=[m.vertex_groups[g.group].name for g in v.groups if g.weight>.5]
 owners.append((int(next(n[4:] for n in names if n.startswith('Part'))),'HeadSource' in names))
co=np.array([v.co[:] for v in m.data.vertices]);arm=bpy.data.armatures.new('Turtle_Rig');rig=bpy.data.objects.new('Turtle_Rig',arm);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');B={};spec={}
def bone(n,a,b,parent=None):
 eb=arm.edit_bones.new(n);eb.head=a;eb.tail=b
 if parent:eb.parent=B[parent]
 eb.align_roll(Vector((0,0,1)) if abs((Vector(b)-Vector(a)).normalized().z)<.95 else Vector((0,-1,0)))
 B[n]=eb;spec[n]={'head':list(a),'tail':list(b),'parent':parent}
bone('Root',(0,0,0),(0,0,.1));bone('Shell',(0,.065,.23),(0,-.12,.23),'Root')
neck=[(0,-.19,.225),(0,-.29,.225),(0,-.39,.225),(0,-.49,.235)]
for i in range(3):bone(f'Neck{i+1}',neck[i],neck[i+1],'Shell' if i==0 else f'Neck{i}')
bone('Head',neck[-1],(0,-.635,.245),'Neck3');bone('Jaw',(0,-.535,.228),(0,-.635,.212),'Head')
for side,sg in [('L',1),('R',-1)]:
 bone('Front_'+side,(sg*.08,-.115,.24),(sg*.32,-.105,.13),'Shell');bone('FrontTip_'+side,(sg*.32,-.105,.13),(sg*.55,-.09,.025),'Front_'+side)
 bone('Rear_'+side,(sg*.13,.22,.22),(sg*.25,.30,.155),'Shell');bone('RearTip_'+side,(sg*.25,.30,.155),(sg*.37,.40,.095),'Rear_'+side)
tail=[(0,.31,.215),(0,.48,.195),(0,.65,.17),(0,.81,.16)]
for i in range(3):bone(f'Tail{i+1}',tail[i],tail[i+1],'Shell' if i==0 else f'Tail{i}')
bpy.ops.object.mode_set(mode='OBJECT')
for g in list(m.vertex_groups):m.vertex_groups.remove(g)
groups={n:m.vertex_groups.new(name=n) for n in spec}
def add(i,w):
 total=sum(w.values());assert total>0
 for n,a in w.items():
  if a>1e-6:groups[n].add([i],float(a/total),'REPLACE')
def chain(p,names,width):
 pts=[np.array(spec[n]['head']) for n in names]+[np.array(spec[names[-1]]['tail'])]
 best=(1e6,0,0)
 for j in range(len(names)):
  d=pts[j+1]-pts[j];t=float(np.clip((p-pts[j])@d/(d@d),0,1));distance=np.linalg.norm(p-(pts[j]+t*d))
  if distance<best[0]:best=(distance,j,t)
 _,j,t=best;length=np.linalg.norm(pts[j+1]-pts[j]);w={names[j]:1}
 if j>0 and t*length<width:
  a=.5+.5*t*length/width;w={names[j]:a,names[j-1]:1-a}
 elif j<len(names)-1 and (1-t)*length<width:
  a=.5+.5*(1-t)*length/width;w={names[j]:a,names[j+1]:1-a}
 return w
shell=[]
for i,p in enumerate(co):
 k,h=owners[i];side='L' if p[0]>0 else 'R'
 if k in [2,3]:add(i,chain(p,['Front_'+side,'FrontTip_'+side],.075))
 elif k in [0,5]:add(i,chain(p,['Rear_'+side,'RearTip_'+side],.045))
 elif k==4:add(i,chain(p,['Tail1','Tail2','Tail3'],.07))
 elif k==6:add(i,{'Jaw':1})
 elif h and (p[1]<-.515 or p[2]>.28):
  jaw=float(np.clip((.228-p[2])/.012,0,1))*float(np.clip((-.52-p[1])/.035,0,1))
  add(i,{'Head':1-jaw,'Jaw':jaw})
 elif (h or (p[1]<-.22 and abs(p[0])<.07 and p[2]<.27)):
  w=chain(p,['Neck1','Neck2','Neck3','Head'],.07);root=float(np.clip((-.22-p[1])/.05,0,1));w={n:v*root for n,v in w.items()};w['Shell']=1-root;add(i,w)
 else:add(i,{'Shell':1});shell.append(i)
mod=m.modifiers.new('Armature','ARMATURE');mod.object=rig;m.parent=rig
for f in m.data.polygons:f.use_smooth=True
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 and len(v.groups)<=4 for v in m.data.vertices)
np.save(P/'work/shell_vertices.npy',np.array(shell));np.save(P/'work/rig_vertices.npy',co)
(P/'work/rig_measurements.json').write_text(json.dumps({'bones':spec,'source':'body_geometry_v2','head_vertices':len(head),'rigid_shell_vertices':len(shell),'vertices':len(co),'repairs':['head/horns translated together; neck extended .20 units','rear flippers scaled .65 about roots','front paddles swept laterally 45 degrees','single tail extended 2.9x','small posterior shell holes filled; normals recalculated']},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
import sys
sys.path.insert(0,str(P/'scripts'))
from review_studio import render_views
if '--no-render' not in sys.argv:render_views(m,P/'review/geometry_rig',views=['side','quarter'])
print('RIG',len(spec),len(co),len(head),len(shell),flush=True)
