"""Measured six-limb rig; isolate membrane weights from torso and bind rigid spikes to their roots."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/clean_v1.blend'));o=bpy.data.objects['Body'];me=o.data
co=np.array([v.co[:] for v in me.vertices]);pa=np.array([v.value for v in me.attributes['part'].data]);wing=((abs(co[:,0])>.15)&(co[:,2]>.31)&(co[:,1]>-.23)&(co[:,1]<.25))|np.isin(pa,[2,4]);head=(abs(co[:,0])<.12)&(co[:,2]>.636)&(co[:,1]<-.25)&(~wing)
# The split follows the underside of the real lower jaw, not the long neck.
jaw=head&(co[:,1]<-.405)&(co[:,2]<.660)
bones={}
def chain(names,points,parent):
 for i,name in enumerate(names):bones[name]=(np.array(points[i]),np.array(points[i+1]),parent if i==0 else names[i-1])
chain(['Root'],[(0,.03,.27),(0,.03,.37)],None)
chain(['Spine1','Spine2'],[(0,.03,.27),(0,-.12,.30),(0,-.27,.37)],'Root')
chain(['Neck1','Neck2','Neck3'],[(0,-.27,.37),(0,-.29,.47),(0,-.29,.57),(0,-.35,.66)],'Spine2')
chain(['Head'],[(0,-.35,.66),(0,-.49,.675)],'Neck3')
chain(['Jaw'],[(0,-.388,.655),(0,-.49,.630)],'Head')
yvals=np.linspace(.03,1.30,10);tailpts=[(0,.03,.27)]
for y in yvals[1:]:
 a=co[(abs(co[:,1]-y)<.06)&(abs(co[:,0])<.09)&(~wing)];tailpts.append((float(np.median(a[:,0])),float(y),float(np.quantile(a[:,2],.42))))
chain([f'Tail{i}' for i in range(1,10)],tailpts,'Root')
for side,sg in [('L',1),('R',-1)]:
 chain([side+'Wing0',side+'Wing1',side+'Wing2'],[(sg*.10,-.15,.41),(sg*.53,-.12,.78),(sg*.99,.00,.91),(sg*1.30,.02,.925)],'Spine2')
 chain([side+'ForeUpper',side+'ForeLower',side+'ForeFoot'],[(sg*.085,-.26,.33),(sg*.12,-.285,.205),(sg*.135,-.445,.13),(sg*.14,-.49,.085)],'Spine2')
 chain([side+'HindUpper',side+'HindLower',side+'HindFoot'],[(sg*.064,.07,.275),(sg*.080,.11,.155),(sg*.115,.22,.085),(sg*.116,.23,.025)],'Root')
arm=bpy.data.armatures.new('Rig');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);o.select_set(False);bpy.ops.object.mode_set(mode='EDIT')
for name,(h,t,parent) in bones.items():
 b=arm.edit_bones.new(name);b.head=h;b.tail=t;b.align_roll(Vector((0,0,1)));b.parent=arm.edit_bones.get(parent) if parent else None
bpy.ops.object.mode_set(mode='OBJECT');groups={n:o.vertex_groups.new(name=n) for n in bones}
def distseg(p,h,t):
 d=t-h;u=np.clip(np.dot(p-h,d)/np.dot(d,d),0,1);return np.linalg.norm(p-(h+u*d))
def weights(p,names):
 ds=np.array([distseg(p,*bones[n][:2]) for n in names]);best=ds.min();ix=np.argsort(ds)[:3];w=np.exp(-((ds[ix]-best)/.028)**2);w[w<.025]=0;w/=w.sum();return {names[j]:float(v) for j,v in zip(ix,w) if v>0}
body_names=['Spine1','Spine2','Neck1','Neck2','Neck3','Head']+[f'Tail{i}' for i in range(1,10)]
W=[]
for i,p in enumerate(co):
 side='L' if p[0]>0 else 'R'
 if wing[i]:
  x=abs(p[0]);stations=[.06,.29,.76,1.19];names=['Spine2',side+'Wing0',side+'Wing1',side+'Wing2'];w={n:float(np.interp(x,stations,np.eye(4)[k])) for k,n in enumerate(names)}
 elif head[i]:w={'Jaw':1.} if jaw[i] else {'Head':1.}
 elif pa[i] in [1,3]:w=weights(p,[side+'ForeUpper',side+'ForeLower',side+'ForeFoot'])
 elif p[2]<.27 and p[1]>.055 and p[1]<.27 and abs(p[0])>.035:
  w=weights(p,[side+'HindUpper',side+'HindLower',side+'HindFoot','Spine1'])
 else:w=weights(p,body_names)
 W.append({n:v for n,v in w.items() if v>.001})
# Disconnected horns/claws/spikes use their nearest attachment weights; long crest follows its body chain.
mainids=np.where(np.isin(pa,[0,1,2,3,4]))[0];tree=kdtree.KDTree(len(mainids))
for i in mainids:tree.insert(Vector(co[i]),int(i))
tree.balance()
for part in sorted(set(pa)):
 ids=np.where(pa==part)[0]
 if part<6:continue
 if head[ids].all():
  w={'Head':1.}
 else:
  anchor=min((tree.find(Vector(co[i])) for i in ids),key=lambda q:q[2])[1];w=W[anchor]
 for i in ids:W[i]=w
for i,w in enumerate(W):
 total=sum(w.values());assert total>0
 for name,value in w.items():groups[name].add([i],value/total,'REPLACE')
o.parent=rig;mod=o.modifiers.new('Armature','ARMATURE');mod.object=rig
# Mouth socket is a deform bone, avoiding Blender bone-parent offset ambiguity on export.
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=arm.edit_bones.new('Socket_Mouth');b.head=(0,-.50,.656);b.tail=(0,-.54,.656);b.parent=arm.edit_bones['Head'];bpy.ops.object.mode_set(mode='OBJECT')
for label,mask in [('wing',wing),('head',head),('jaw',jaw)]:
 attr=me.attributes.new(label,'BOOLEAN','POINT')
 for i,v in enumerate(mask):attr.data[i].value=bool(v)
for i,name in enumerate(['DrakeBody','DrakeHead','DrakeWings']):
 m=bpy.data.materials.new(name);m.use_nodes=True;me.materials.append(m)
# Remove the imported neutral material before assigning domain slots.
while len(me.materials)>3:me.materials.pop(index=0)
for f in me.polygons:
 ids=list(f.vertices);f.material_index=2 if wing[ids].mean()>.5 else (1 if head[ids].mean()>.5 else 0)
np.savez(P/'work/rig_domains.npz',wing=wing,head=head,jaw=jaw)
report={'bones':{n:{'head':h.tolist(),'tail':t.tolist(),'parent':p} for n,(h,t,p) in bones.items()},'unweighted':sum(not v.groups for v in me.vertices),'max_influences':max(len(v.groups) for v in me.vertices),'domain_vertices':{'wing':int(wing.sum()),'head':int(head.sum()),'jaw':int(jaw.sum())}}
assert report['unweighted']==0 and report['max_influences']<=4
(P/'work/rig_report.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'));print('RIG',len(bones),report['domain_vertices'])
