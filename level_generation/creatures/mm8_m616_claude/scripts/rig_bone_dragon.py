"""Fit the exposed skeleton with rigid shafts and short joint blends; membranes have their own ownership."""
import bpy,json,math,heapq
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/static_v1.blend'))
o=bpy.data.objects['BoneDragon'];co=np.array([v.co[:] for v in o.data.vertices]);x,y,z=co.T
bones={}
def chain(names,points,parent):
 for i,n in enumerate(names):bones[n]=(np.array(points[i],float),np.array(points[i+1],float),parent if i==0 else names[i-1])
chain(['Root'],[(0,-.035,.26),(0,-.035,.30)],None)
chain(['Chest'],[(0,-.035,.26),(0,-.165,.30)],'Root')
chain(['Neck1','Neck2','Neck3'],[(0,-.165,.30),(-.004,-.18,.34),(-.006,-.19,.375),(-.007,-.22,.409)],'Chest')
chain(['Head'],[(-.007,-.22,.409),(-.007,-.31,.392)],'Neck3')
chain(['Jaw'],[(-.007,-.244,.374),(-.007,-.315,.349)],'Head')
tail=[(0,-.035,.26)]
for yy in np.linspace(.01,.325,10):
 cloud=co[(abs(y-yy)<.014)&(z>.14)]
 tail.append((float(np.median(cloud[:,0])),float(yy),float(np.quantile(cloud[:,2],.4))))
chain([f'Tail{i}' for i in range(1,11)],tail,'Root')
for side,sg in [('L',1),('R',-1)]:
 chain([side+'WingUpper',side+'WingFore',side+'WingHand'],[(sg*.062,-.155,.311),(sg*.168,-.15,.388),(sg*.189,-.222,.477),(sg*.30,-.208,.49)],'Chest')
 tips=[(.574,-.226,.493),(.574,-.211,.373),(.50,-.182,.30),(.345,-.135,.29)]
 for i,t in enumerate(tips):chain([f'{side}WingFinger{i+1}'],[(sg*.189,-.222,.477),(sg*t[0],t[1],t[2])],side+'WingHand')
 if sg>0:
  front=[(.047,-.166,.293),(.074,-.198,.191),(.089,-.279,.207),(.104,-.314,.17)]
  hind=[(.045,-.019,.248),(.054,-.051,.16),(.067,.003,.12),(.073,-.032,.047)]
 else:
  front=[(-.048,-.155,.292),(-.063,-.145,.205),(-.069,-.227,.122),(-.074,-.242,.078)]
  hind=[(-.045,-.025,.247),(-.06,-.064,.16),(-.078,.001,.149),(-.072,.006,.07)]
 chain([side+'ForeUpper',side+'ForeLower',side+'ForeFoot'],front,'Chest')
 chain([side+'HindUpper',side+'HindLower',side+'HindFoot'],hind,'Root')
chain(['Socket_Mouth'],[(-.007,-.308,.379),(-.007,-.328,.379)],'Head')
arm=bpy.data.armatures.new('BoneDragon_Rig');rig=bpy.data.objects.new('BoneDragon_Rig',arm);bpy.context.collection.objects.link(rig)
for ob in bpy.context.scene.objects:ob.select_set(ob==rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n,(h,t,parent) in bones.items():
 b=arm.edit_bones.new(n);b.head=h;b.tail=t;b.align_roll(Vector((0,0,1)));b.parent=arm.edit_bones.get(parent) if parent else None
bpy.ops.object.mode_set(mode='OBJECT');groups={n:o.vertex_groups.new(name=n) for n in bones}
wing=((abs(x)>.061)&(z>.290)&(y<-.105))|((abs(x)>.12)&(z>.26))
head=((y<-.241)&(z>.30))|((y<-.14)&(z>.385)&(abs(x)<.061))
adj=[[] for _ in co]
for e in o.data.edges:
 a,b=e.vertices;length=float(np.linalg.norm(co[a]-co[b]));adj[a].append((b,length));adj[b].append((a,length))
def distance_field(seeds,allowed):
 dist=np.full(len(co),np.inf);queue=[]
 for i in np.where(seeds)[0]:dist[i]=0.;heapq.heappush(queue,(0.,int(i)))
 while queue:
  d,i=heapq.heappop(queue)
  if d>dist[i]:continue
  for j,l in adj[i]:
   if allowed[j] and d+l<dist[j]:dist[j]=d+l;heapq.heappush(queue,(d+l,j))
 return dist
jd=distance_field(head&(y<-.29)&(z<.35),head)
hd=distance_field(head&(y<-.29)&(z>.39),head)
jaw=head&(jd<hd)
fore=(y<-.205)&(z<.255)|(y<-.10)&(z<.195)|((abs(x)>.056)&(y<-.115)&(z<.302))
hind=(y>-.1)&(y<.08)&(z<.20)|((abs(x)>.03)&(y>-.065)&(y<.03)&(z<.255))
# The central lower ribs must remain on the thorax even beside the elbows.
fore&=~((abs(x)<.055)&(y>-.20)&(z>.195))
labels=np.zeros(len(co),dtype=np.int32);weights=[]
def ds(p,n):
 h,t,_=bones[n];d=t-h;u=np.clip(np.dot(p-h,d)/np.dot(d,d),0,1);return np.linalg.norm(p-h-u*d)
def choose(p,names,width=.006):
 dist=np.array([ds(p,n) for n in names]);order=np.argsort(dist)[:2]
 w=np.exp(-((dist[order]-dist.min())/width)**2);w[w<.02]=0;w/=w.sum()
 return {names[i]:float(v) for i,v in zip(order,w) if v>0}
for i,p in enumerate(co):
 side='L' if p[0]>0 else 'R'
 if wing[i]:
  labels[i]=1 if p[0]>0 else 2
  names=[side+'WingUpper',side+'WingFore']+[f'{side}WingFinger{j}' for j in range(1,5)]
  w=choose(p,names,.024)
  blend=float(np.clip((abs(p[0])-.052)/.035,0,1))
  w={n:v*blend for n,v in w.items() if v*blend>.0001}
  if blend<1:w['Chest']=1-blend
 elif head[i]:labels[i]=3;w={'Jaw' if jaw[i] else 'Head':1.}
 elif fore[i]:labels[i]=4 if p[0]>0 else 5;w=choose(p,[side+'ForeUpper',side+'ForeLower',side+'ForeFoot'])
 elif hind[i]:labels[i]=6 if p[0]>0 else 7;w=choose(p,[side+'HindUpper',side+'HindLower',side+'HindFoot'])
 elif p[1]>.008:labels[i]=8;w=choose(p,[f'Tail{j}' for j in range(1,11)],.004)
 elif p[2]>.31:labels[i]=9;w=choose(p,['Chest','Neck1','Neck2','Neck3','Head'],.004)
 else:w={'Chest' if p[1]<-.045 else 'Root':1.}
 weights.append(w)
# Loose vertebra spines follow one anatomical owner; no nearest-wing or limb drift.
adj=[[] for _ in co]
for e in o.data.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();components=[]
for v in range(len(co)):
 if v in seen:continue
 stack=[v];seen.add(v);ids=[]
 while stack:
  q=stack.pop();ids.append(q)
  for j in adj[q]:
   if j not in seen:seen.add(j);stack.append(j)
 components.append(ids)
for ids in components:
 if len(ids)>100 or np.any(wing[ids]):continue
 totals={}
 for i in ids:
  for n,w in weights[i].items():totals[n]=totals.get(n,0)+w
 owner=max(totals,key=totals.get)
 for i in ids:weights[i]={owner:1.}
# Smooth only anatomical ownership boundaries, keeping isolated bone shafts rigid.
for iteration in range(4):
 changed=[]
 for i,w in enumerate(weights):
  if labels[i]==3 or not adj[i]:changed.append(w);continue
  totals={n:v*.55 for n,v in w.items()}
  for j in adj[i]:
   for n,v in weights[j].items():totals[n]=totals.get(n,0)+.45*v/len(adj[i])
  totals=dict(sorted(totals.items(),key=lambda item:item[1],reverse=True)[:4]);total=sum(totals.values())
  changed.append({n:v/total for n,v in totals.items() if v/total>.001})
  total=sum(changed[-1].values());changed[-1]={n:v/total for n,v in changed[-1].items()}
 weights=changed
for i,w in enumerate(weights):
 assert 0<len(w)<=4 and abs(sum(w.values())-1)<1e-6
 for n,v in w.items():groups[n].add([i],v,'REPLACE')
attr=o.data.attributes.new('anatomy_part','INT','POINT')
for d,v in zip(attr.data,labels):d.value=int(v)
mod=o.modifiers.new('Skeleton','ARMATURE');mod.object=rig;o.parent=rig
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
(P/'work/rig.json').write_text(json.dumps({'bones':{n:{'head':h.tolist(),'tail':t.tolist(),'parent':p} for n,(h,t,p) in bones.items()},'vertices':len(co),'components':len(components),'maximum_influences':max(map(len,weights))},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
print('RIG',len(bones),'bones',len(co),'vertices')
