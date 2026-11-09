"""Measured six-limb dragon rig; keep membranes and leg roots out of the neck weights."""
import bpy, bmesh, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector, kdtree
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/static_v1.blend'))
o = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(o.data)
part = bm.verts.layers.int['part']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[part] in (54,55,56)], context='VERTS')
# Open the fused lips on their measured seam; keep the upper muzzle on Head.
seam_origin=Vector((0,-.395,.281));seam_normal=Vector((0,-.25,1))
faces=[f for f in bm.faces if all(v[part]==0 for v in f.verts) and
       all(v.co.y<-.333 and v.co.z<.323 for v in f.verts)]
geom=set(faces)
for f in faces:geom.update(f.edges);geom.update(f.verts)
cut=bmesh.ops.bisect_plane(bm,geom=list(geom),dist=1e-7,plane_co=seam_origin,plane_no=seam_normal)
edges=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge)]
bmesh.ops.split_edges(bm,edges=edges)
jaw_layer=bm.verts.layers.int.new('lower_jaw')
oral=bm.faces.layers.int.new('oral')
for f in bm.faces:
 c=f.calc_center_median()
 if all(v[part]==0 for v in f.verts) and c.y<-.333 and (c-seam_origin).dot(seam_normal)<-1e-7:
  for v in f.verts:v[jaw_layer]=1
# A dark inner palate and jaw floor close the newly separated lip shells.
for lower in (False,True):
 border=[e for e in bm.edges if e.is_boundary and e.verts[0].co.y<-.333 and e.verts[1].co.y<-.333
         and all(abs((v.co-seam_origin).dot(seam_normal))<2e-6 for v in e.verts)
         and bool(e.verts[0][jaw_layer] and e.verts[1][jaw_layer])==lower]
 if not border:continue
 center=bm.verts.new((0,-.334,.2965));center[part]=0;center[jaw_layer]=int(lower)
 for e in border:
  a,b=e.verts
  f=bm.faces.new((a,b,center) if lower else (b,a,center));f[oral]=1
# Rebuild the small upper teeth lost in the fused lip seam, with rigid skull ownership.
for sg in (-1,1):
 for j,yy in enumerate(np.linspace(-.387,-.349,7)):
  xx=sg*(.0065+.006*j/6);zz=.281+.25*(yy+.395)+.0012
  radius=.0009 if j<2 else .0013;length=.0035 if j<3 else .005
  ring=[bm.verts.new((xx+radius*math.cos(k*math.tau/6),yy+radius*math.sin(k*math.tau/6),zz)) for k in range(6)]
  tip=bm.verts.new((xx,yy-.0006,zz-length))
  for v in ring+[tip]:v[part]=57;v[jaw_layer]=0
  for k in range(6):bm.faces.new((ring[k],ring[(k+1)%6],tip))
  bm.faces.new(tuple(reversed(ring)))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(o.data);bm.free()
me=o.data; co=np.array([v.co[:] for v in me.vertices]); pa=np.array([v.value for v in me.attributes['part'].data])
x,y,z=co.T
wing=(abs(x)>.04)&(z>.165)&(y>-.27)&(y<-.06)
head=((z>.275)&(y<-.278)|(z>.26)&(y<-.333))&(~wing)
head |= np.isin(pa,[3,4,7,8,9,10,11,12,13])
jaw=np.array([v.value for v in me.attributes['lower_jaw'].data],dtype=bool)
fore=(y<-.185)&(z<.18)&(~wing)
hind=(y>-.185)&(y<.055)&(z<.155)&(~wing)
bones={}
def chain(names, points, parent):
 for i,n in enumerate(names):
  bones[n]=(np.array(points[i]),np.array(points[i+1]),parent if i==0 else names[i-1])
chain(['Root'],[(0,-.13,.15),(0,-.13,.19)],None)
chain(['Spine1','Spine2'],[(0,-.13,.15),(0,-.20,.16),(0,-.255,.175)],'Root')
chain(['Neck1','Neck2','Neck3'],[(0,-.255,.175),(0,-.275,.225),(0,-.26,.28),(0,-.305,.313)],'Spine2')
chain(['Head'],[(0,-.305,.313),(0,-.389,.29)],'Neck3')
chain(['Jaw'],[(0,-.334,.296),(0,-.393,.279)],'Head')
tailpts=[(0,-.13,.15)]
for yy in np.linspace(-.075,.415,10):
 a=co[(abs(y-yy)<.023)&(abs(x)<.018)&(z>.1)&(~wing)]
 tailpts.append((float(np.median(a[:,0])),float(yy),float(np.quantile(a[:,2],.35))))
chain([f'Tail{i}' for i in range(1,11)],tailpts,'Root')
for side,sg in [('L',1),('R',-1)]:
 chain([side+'Wing0',side+'Wing1',side+'Wing2',side+'Wing3'],
       [(sg*.043,-.205,.183),(sg*.11,-.205,.226),(sg*.18,-.222,.32),
        (sg*.32,-.172,.385),(sg*.473,-.13,.423)],'Spine2')
 chain([side+'ForeUpper',side+'ForeLower',side+'ForeFoot'],
       [(sg*.043,-.255,.16),(sg*.05,-.25,.104),(sg*.055,-.303,.065),(sg*.06,-.327,.04)],'Spine2')
 chain([side+'HindUpper',side+'HindLower',side+'HindFoot'],
       [(sg*.039,-.13,.15),(sg*.054,-.12,.087),(sg*.06,-.06,.074),(sg*.06,-.036,.013)],'Root')
chain(['Socket_Mouth'],[(0,-.372,.287),(0,-.392,.28)],'Head')
arm=bpy.data.armatures.new('Rig');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for n,(h,t,parent) in bones.items():
 b=arm.edit_bones.new(n);b.head=h;b.tail=t;b.align_roll(Vector((0,0,1)))
 b.parent=arm.edit_bones.get(parent) if parent else None
bpy.ops.object.mode_set(mode='OBJECT')
groups={n:o.vertex_groups.new(name=n) for n in bones}
def distance(p,h,t):
 d=t-h;u=np.clip(np.dot(p-h,d)/np.dot(d,d),0,1);return np.linalg.norm(p-h-u*d)
def blend(p,names,width=.012):
 ds=np.array([distance(p,*bones[n][:2]) for n in names]);ix=np.argsort(ds)[:4]
 w=np.exp(-((ds[ix]-ds.min())/width)**2);w[w<.025]=0;w/=w.sum()
 return {names[j]:float(v) for j,v in zip(ix,w) if v>0}
body=['Spine1','Spine2','Neck1','Neck2','Neck3','Head']+[f'Tail{i}' for i in range(1,11)]
W=[]
for i,p in enumerate(co):
 side='L' if p[0]>0 else 'R'
 if wing[i]:
  stations=[.035,.077,.155,.27,.41];names=['Spine2']+[side+f'Wing{j}' for j in range(4)]
  w={n:float(np.interp(abs(p[0]),stations,np.eye(5)[k])) for k,n in enumerate(names)}
  root=float(np.clip((abs(p[0])-.04)/.045,0,1));root=root*root*(3-2*root)
  body_w=blend(p,body,.012)
  w={n:root*w.get(n,0)+(1-root)*body_w.get(n,0) for n in set(w)|set(body_w)}
  w=dict(sorted(w.items(),key=lambda q:q[1],reverse=True)[:4])
 elif head[i]:
  j=float(np.clip((-.335-p[1])/.015,0,1)) if jaw[i] else 0.;j=j*j*(3-2*j)
  w={'Jaw':j,'Head':1-j}
  if not jaw[i] and pa[i]==0 and p[1]>-.315 and p[2]<.315:
   w=blend(p,['Neck2','Neck3','Head'],.012)
 elif fore[i] and p[1]<-.298 and p[2]<.085:w={side+'ForeFoot':1.}
 elif hind[i] and p[2]<.06:w={side+'HindFoot':1.}
 elif fore[i]:w=blend(p,[side+'ForeUpper',side+'ForeLower',side+'ForeFoot']+body,.018)
 elif hind[i]:w=blend(p,[side+'HindUpper',side+'HindLower',side+'HindFoot','Spine1','Tail1','Tail2','Tail3'],.018)
 else:w=blend(p,body,.012)
 W.append({n:v for n,v in w.items() if v>.001})
# Blend only connected soft leg roots; the toe tips, horns and wing spars keep their ownership.
adj=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
soft=(pa==0)&(~wing)&(~head)&(z>.085)&(z<.185)&(y>-.32)&(y<.055)
for _ in range(5):
 old=W;W=list(old)
 for i in np.where(soft)[0]:
  if not adj[i]:continue
  w={n:v*.5 for n,v in old[i].items()}
  for j in adj[i]:
   for n,v in old[j].items():w[n]=w.get(n,0)+v*.5/len(adj[i])
  w=dict(sorted(w.items(),key=lambda q:q[1],reverse=True)[:4]);total=sum(w.values());W[i]={n:v/total for n,v in w.items()}
# Separate horn/spine shells follow the attachment, while long wing spars keep their spanwise weights.
main=np.where(pa==0)[0];tree=kdtree.KDTree(len(main))
for i in main:tree.insert(Vector(co[i]),int(i))
tree.balance()
for part in sorted(set(pa)):
 if part in (0,1,2,5,6,49,50):continue
 ids=np.where(pa==part)[0]
 if head[ids].all():w={'Head':1.}
 else:
  anchor=min((tree.find(Vector(co[i])) for i in ids),key=lambda q:q[2])[1];w=W[anchor]
 for i in ids:W[i]=w
for i,w in enumerate(W):
 total=sum(w.values());assert total>0
 for n,v in w.items():groups[n].add([i],v/total,'REPLACE')
o.parent=rig;mod=o.modifiers.new('Armature','ARMATURE');mod.object=rig
for label,mask in [('wing',wing),('head',head),('jaw',jaw),('fore',fore),('hind',hind)]:
 attr=me.attributes.new(label,'BOOLEAN','POINT')
 for i,v in enumerate(mask):attr.data[i].value=bool(v)
me.materials.clear()
for name,color in [('DragonBody',(.35,.35,.35,1)),('DragonHead',(.6,.6,.6,1)),('DragonWings',(.55,.45,.25,1)),('DragonMouth',(.06,.012,.015,1))]:
 m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True;me.materials.append(m)
for f in me.polygons:
 ids=list(f.vertices);f.material_index=3 if me.attributes['oral'].data[f.index].value else (2 if wing[ids].mean()>.5 else (1 if head[ids].mean()>.5 else 0))
report={'bones':{n:{'head':h.tolist(),'tail':t.tolist(),'parent':p} for n,(h,t,p) in bones.items()},
        'unweighted':sum(not v.groups for v in me.vertices),'max_influences':max(len(v.groups) for v in me.vertices),
        'triangles':sum(len(f.vertices)-2 for f in me.polygons),'vertices':len(co),
        'domains':{n:int(a.sum()) for n,a in [('wing',wing),('head',head),('jaw',jaw),('fore',fore),('hind',hind)]}}
assert report['unweighted']==0 and report['max_influences']<=4
(P/'work/rig_report.json').write_text(json.dumps(report,indent=2)+'\n')
np.savez(P/'work/rig_domains.npz',co=co,wing=wing,head=head,jaw=jaw,fore=fore,hind=hind)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
print('RIG',report['triangles'],report['domains'])
