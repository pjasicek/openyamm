"""Repair measured m556 geometry and fit a local insect rig. Component ids bind this to body_geometry_v1."""
from pathlib import Path
import bpy,bmesh,json,math
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_v1.blend'))
m=bpy.data.objects['Wasp'];labels=np.load(P/'work/components.npy')
assert len(m.data.vertices)==len(labels)==8113
for k in range(int(labels.max())+1):m.vertex_groups.new(name=f'Source_{k}').add(np.where(labels==k)[0].tolist(),1,'REPLACE')
# Collapse the unsupported rear thorax spur, keeping the real petiole/abdomen below it.
repaired=0
for v in m.data.vertices:
 if labels[v.index]==1 and v.co.z>.505 and v.co.y>.065:
  v.co.y=.065+(v.co.y-.065)*.055;repaired+=1
# Reconnect each short middle leg to its own coxa, not the upper arm's elbow.
for k,sign in [(9,-1),(10,1)]:
 q=np.array([v.co[:] for v in m.data.vertices if labels[v.index]==k]);top=q[q[:,2]>q[:,2].max()-.009].mean(0)
 target=np.array((sign*.101,.026,.480));delta=target-top
 for v in m.data.vertices:
  if labels[v.index]==k:v.co+=Vector(delta)
# Replace the thick scalloped Meshy membranes with two thin continuous native leaf silhouettes.
bm=bmesh.new();bm.from_mesh(m.data);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if labels[v.index] in (4,8,25)],context='VERTS')
bm.to_mesh(m.data);bm.free()
for side,sign in [('L',1),('R',-1)]:
 root=Vector((sign*.055,.027,.601));tip=Vector((sign*.500,.013,.905));axis=tip-root
 across=Vector((-sign*.564,0,.826));verts=[];faces=[];N=22;C=4
 for layer in [-1,1]:
  for i in range(N+1):
   t=i/N;width=.108*math.sin(math.pi*t)**.85*(.8+.30*t)+.0008
   for j in range(C+1):
    u=j/C-.5;v=root+axis*t+across*(width*u);v.y+=.008*math.sin(math.pi*t)*(u*2)**2+layer*.00055
    verts.append(v)
 count=(N+1)*(C+1)
 for layer in range(2):
  for i in range(N):
   for j in range(C):
    a=layer*count+i*(C+1)+j;f=(a,a+1,a+C+2,a+C+1);faces.append(f if layer==0 else f[::-1])
 perimeter=list(range(C+1))+[i*(C+1)+C for i in range(1,N+1)]+[N*(C+1)+j for j in range(C-1,-1,-1)]+[i*(C+1) for i in range(N-1,0,-1)]
 for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):faces.append((a,b,b+count,a+count))
 data=bpy.data.meshes.new('Wing_'+side);data.from_pydata(verts,[],faces);data.update();obj=bpy.data.objects.new('Wing_'+side,data);bpy.context.collection.objects.link(obj)
 obj.vertex_groups.new(name='WingSource_'+side).add(list(range(len(verts))),1,'REPLACE')
 bpy.ops.object.select_all(action='DESELECT');m.select_set(True);obj.select_set(True);bpy.context.view_layer.objects.active=m;bpy.ops.object.join()
co=np.array([v.co[:] for v in m.data.vertices]);source={g.index:g.name for g in m.vertex_groups}
owners=[next((source[g.group] for g in v.groups if g.weight>.5),'') for v in m.data.vertices]
assert all(owners)
arm=bpy.data.armatures.new('Wasp_Rig');rig=bpy.data.objects.new('Wasp_Rig',arm);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');B={};spec={}
def bone(n,a,b,parent=None):
 a,b=Vector(a),Vector(b);eb=arm.edit_bones.new(n);eb.head=a;eb.tail=b
 if parent:eb.parent=B[parent]
 eb.align_roll(Vector((0,0,1)) if abs((b-a).normalized().z)<.94 else Vector((0,-1,0)))
 B[n]=eb;spec[n]=dict(head=list(a),tail=list(b),parent=parent)
 return n
bone('Root',(0,0,0),(0,0,.1))
bone('Thorax',(0,.03,.50),(0,-.035,.635),'Root')
bone('Neck',(0,-.035,.635),(0,-.132,.697),'Thorax')
bone('Head',(0,-.132,.697),(0,-.255,.68),'Neck')
abd=[(0,.075,.472),(0,.139,.375),(0,.221,.263),(0,.314,.136),(0,.418,.005)]
for i in range(4):bone('Abdomen'+str(i+1),abd[i],abd[i+1],'Thorax' if i==0 else 'Abdomen'+str(i))
for side,sg in [('L',1),('R',-1)]:
 def s(v):return (sg*v[0],v[1],v[2])
 armpts=[s((.056,-.034,.586)),s((.146,.006,.531)),s((.245,-.076,.485)),s((.267,-.087,.464))]
 for i,n in enumerate(['UpperArm','ForeArm','Hand']):bone(n+'_'+side,armpts[i],armpts[i+1],'Thorax' if i==0 else ['UpperArm','ForeArm'][i-1]+'_'+side)
 # Three measured claw branches share the palm but retain separate distal controls.
 for digit,x in enumerate([.232,.261,.287]):bone(f'Claw{digit+1}_{side}',s((x,-.086,.477)),s((x,-.092,.443)),'Hand_'+side)
 mid=[s((.049,.028,.522)),s((.101,.026,.480)),s((.111,.037,.400)),s((.140,.029,.339))]
 for i,n in enumerate(['MidFemur','MidTibia','MidTarsus']):bone(n+'_'+side,mid[i],mid[i+1],'Thorax' if i==0 else ['MidFemur','MidTibia'][i-1]+'_'+side)
 hind=[s((.029,.110,.500)),s((.095,.104,.415)),s((.199,.091,.245)),s((.260,.090,.112)),s((.280,.089,.036))]
 for i,n in enumerate(['HindCoxa','HindFemur','HindTibia','HindTarsus']):bone(n+'_'+side,hind[i],hind[i+1],'Thorax' if i==0 else ['HindCoxa','HindFemur','HindTibia'][i-1]+'_'+side)
 bone('WingRoot_'+side,s((.055,.027,.601)),s((.290,.020,.762)),'Thorax');bone('WingFlex_'+side,s((.290,.020,.762)),s((.500,.013,.905)),'WingRoot_'+side)
 ant=[s((.025,-.197,.761)),s((.050,-.270,.841)),s((.066,-.346,.868)),s((.072,-.416,.856))]
 for i in range(3):bone(f'Antenna{i+1}_{side}',ant[i],ant[i+1],'Head' if i==0 else f'Antenna{i}_{side}')
 bone('Mandible_'+side,s((.025,-.247,.661)),s((.026,-.292,.624)),'Head')
bone('Sword',(.263,-.091,.459),(.263,-.191,.459),'Hand_L')
bone('Shield',(-.263,-.101,.459),(-.263,-.201,.459),'Hand_R')
bpy.ops.object.mode_set(mode='OBJECT')
for g in list(m.vertex_groups):m.vertex_groups.remove(g)
groups={n:m.vertex_groups.new(name=n) for n in spec}
def add(i,weights):
 total=sum(weights.values());assert total>0
 for n,w in weights.items():
  if w>1e-5:groups[n].add([i],float(w/total),'REPLACE')
def chain(p,names,width=.012):
 # Arc-length segmentation keeps hard plates rigid; only the small joint bridge blends.
 pts=[np.array(spec[n]['head']) for n in names]+[np.array(spec[names[-1]]['tail'])]
 best=(1e9,0,0.)
 for j in range(len(names)):
  d=pts[j+1]-pts[j];t=float(np.clip((p-pts[j])@d/(d@d),0,1));dist=np.linalg.norm(p-(pts[j]+t*d))
  if dist<best[0]:best=(dist,j,t)
 _,j,t=best;out={names[j]:1.};length=np.linalg.norm(pts[j+1]-pts[j])
 if j>0 and t*length<width:
  a=.5+.5*t*length/width;out={names[j]:a,names[j-1]:1-a}
 elif j<len(names)-1 and (1-t)*length<width:
  a=.5+.5*(1-t)*length/width;out={names[j]:a,names[j+1]:1-a}
 return out
for i,p in enumerate(co):
 owner=owners[i];sg='L' if p[0]>=0 else 'R';k=int(owner[7:]) if owner.startswith('Source_') else -1
 if owner.startswith('WingSource_'):add(i,chain(p,['WingRoot_'+sg,'WingFlex_'+sg],.055))
 elif k in [0,2,11,23,18,19,20,21]:add(i,chain(p,[n+'_'+sg for n in ['HindCoxa','HindFemur','HindTibia','HindTarsus']]))
 elif k in [3,9,10,17,22,24]:add(i,chain(p,[n+'_'+sg for n in ['MidFemur','MidTibia','MidTarsus']],.009))
 elif k in [5,6]:
  if p[2]<.477 and abs(p[0])>.212:
   d=min(range(3),key=lambda d:abs(abs(p[0])-[.232,.261,.287][d]));w=float(np.clip((.477-p[2])/.012,0,1));add(i,{f'Claw{d+1}_{sg}':w,'Hand_'+sg:1-w})
  else:add(i,chain(p,[n+'_'+sg for n in ['UpperArm','ForeArm','Hand']],.014))
 elif k in [7,15]:add(i,{'UpperArm_'+sg:.7,'Thorax':.3})
 elif k in [12,14]:add(i,chain(p,[f'Antenna{j}_{sg}' for j in range(1,4)],.018))
 elif k in [13,16]:add(i,{'Mandible_'+sg:1})
 elif k==1:
  if p[2]<.48 and p[1]>.04:add(i,chain(p,['Abdomen'+str(j) for j in range(1,5)],.025))
  elif p[1]<-.13:
   w=float(np.clip((-.10-p[1])/.06,0,1));add(i,{'Head':w,'Neck':1-w})
  elif p[2]>.63:
   w=float(np.clip((p[2]-.63)/.04,0,1));add(i,{'Neck':w,'Thorax':1-w})
  else:add(i,{'Thorax':1})
 else:raise AssertionError((i,owner))
mod=m.modifiers.new('Armature','ARMATURE');mod.object=rig;m.parent=rig
for f in m.data.polygons:f.use_smooth=True
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in m.data.vertices)
(P/'work/rig_measurements.json').write_text(json.dumps(dict(bones=spec,thorax_spur_vertices=repaired,vertices=len(co),method='Measured component junctions and coordinate-slice centroids; local membrane silhouette repair; normalized exoskeleton weights.'),indent=2))
np.save(P/'work/repaired_vertices.npy',co)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
print('RIG',len(spec),'bones',len(co),'vertices, unweighted=0')
