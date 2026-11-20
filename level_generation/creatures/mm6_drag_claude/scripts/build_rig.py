import bpy,json,math,bmesh,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/clean_v1.blend'));o=bpy.data.objects['Body'];me=o.data
parts=np.array([v.value for v in me.attributes['part'].data]);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
# Replace the blunt generated forehead horn with a tapered low-poly horn.
bmesh.ops.delete(bm,geom=[v for v in bm.verts if parts[v.index]==4],context='VERTS');bm.to_mesh(me);bm.free()
bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=.019,radius2=0,depth=.085,location=(-.004,-.344,.873));horn=bpy.context.object;horn.rotation_euler[0]=-.22
bpy.ops.object.select_all(action='DESELECT');horn.select_set(True);o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join();me=o.data
co=np.array([v.co[:] for v in me.vertices]);parts=np.array([v.value for v in me.attributes['part'].data]);bones={}
def chain(names,pts,parent):
 for i,n in enumerate(names):bones[n]=(np.array(pts[i],float),np.array(pts[i+1],float),names[i-1] if i else parent)
chain(['Root'],[(0,-.20,.28),(0,-.22,.37)],None)
chain(['Spine1','Spine2'],[(0,-.20,.28),(0,-.235,.43),(0,-.245,.55)],'Root')
chain(['Neck1','Neck2','Neck3'],[(0,-.245,.55),(0,-.26,.65),(0,-.27,.74),(0,-.30,.815)],'Spine2')
chain(['Head'],[(0,-.30,.815),(0,-.435,.80)],'Neck3')
chain(['Jaw'],[(0,-.345,.787),(0,-.445,.741)],'Head')
pts=[(0,-.20,.28),(0,-.06,.19),(0,.055,.103),(0,.16,.071),(0,.27,.071),(0,.365,.091),(0,.417,.135),(0,.432,.19),(0,.399,.245)]
chain([f'Tail{i}' for i in range(1,9)],pts,'Root')
for side,s in [('L',1),('R',-1)]:
 chain([side+'UpperArm',side+'ForeArm',side+'Hand'],[(s*.075,-.257,.505),(s*.12,-.284,.407),(s*.118,-.372,.375),(s*.12,-.401,.322)],'Spine2')
 chain([side+'Thigh',side+'Shin',side+'Foot'],[(s*.09,-.205,.29),(s*.131,-.265,.161),(s*.144,-.224,.050),(s*.155,-.284,.013)],'Root')
arm=bpy.data.armatures.new('Rig');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n,(h,t,p) in bones.items():
 b=arm.edit_bones.new(n);b.head=h;b.tail=t;b.align_roll(Vector((0,0,1)));b.parent=arm.edit_bones.get(p) if p else None
b=arm.edit_bones.new('Socket_Mouth');b.head=(0,-.46,.78);b.tail=(0,-.50,.78);b.parent=arm.edit_bones['Head'];bpy.ops.object.mode_set(mode='OBJECT');groups={n:o.vertex_groups.new(name=n) for n in bones}
def weights(p,names,width=.030):
 ds=[]
 for n in names:
  h,t,_=bones[n];d=t-h;u=np.clip(np.dot(p-h,d)/np.dot(d,d),0,1);ds.append(np.linalg.norm(p-h-u*d))
 ds=np.array(ds);ii=np.argsort(ds)[:4];w=np.exp(-((ds[ii]-ds[ii[0]])/width)**2);w[w<.02]=0;w/=w.sum();return {names[i]:float(v) for i,v in zip(ii,w) if v>0}
head=(co[:,2]>.79)|((co[:,1]<-.355)&(co[:,2]>.67));jaw=head&(co[:,1]<-.354)&(co[:,2]<np.interp(co[:,1],[-.475,-.36],[.754,.781]))
allw=[]
for i,p in enumerate(co):
 x,y,z=p;s='L' if x>=-.003 else 'R'
 if head[i]:w={'Jaw' if jaw[i] else 'Head':1.}
 elif y>-.07 and z<.38:w=weights(p,[f'Tail{k}' for k in range(1,9)])
 elif .316<z<.49 and abs(x)>.064 and y<-.288:
  w={s+'Hand':1.} if z<.38 and y<-.35 else weights(p,[s+'UpperArm',s+'ForeArm',s+'Hand','Spine2'],.023)
 elif z<.31 and abs(x)>.065 and y<-.12:
  w={s+'Foot':1.} if z<.055 else weights(p,[s+'Thigh',s+'Shin',s+'Foot','Root'],.025)
 else:w=weights(p,['Root','Spine1','Spine2','Neck1','Neck2','Neck3','Head','Tail1'],.036)
 allw.append(w)
# Diffuse ownership over connected skin so coordinate seed boundaries cannot crease the hips/shoulders.
names=list(bones);wi=np.zeros((len(co),len(names)));ni={n:k for k,n in enumerate(names)}
for i,w in enumerate(allw):
 for n,v in w.items():wi[i,ni[n]]=v
edges=np.array([e.vertices[:] for e in me.edges]);aa=np.r_[edges[:,0],edges[:,1]];bb=np.r_[edges[:,1],edges[:,0]];degree=np.bincount(aa,minlength=len(co));mov=(parts==0)&(~head)&(degree>0)
for _ in range(18):
 sums=np.zeros_like(wi);np.add.at(sums,aa,wi[bb]);avg=sums/np.maximum(degree,1)[:,None];wi[mov]=wi[mov]*.35+avg[mov]*.65
for i in np.flatnonzero(mov):
 ids=np.argsort(wi[i])[-4:];ww=wi[i,ids];ww/=ww.sum();allw[i]={names[k]:float(v) for k,v in zip(ids,ww) if v>.005}
 forsum=sum(allw[i].values());allw[i]={n:v/forsum for n,v in allw[i].items()}
# Loose spines/teeth keep coherent weights; teeth follow their own upper or lower jaw.
for part in np.unique(parts):
 if part==0:continue
 ids=np.flatnonzero(parts==part);c=co[ids].mean(0)
 if len(ids)<4:continue
 if c[2]>.75 and c[1]<-.35:w={'Jaw' if c[2]<np.interp(c[1],[-.475,-.36],[.754,.781]) else 'Head':1.}
 elif c[2]>.79:w={'Head':1.}
 else:
  near=np.flatnonzero(parts==0);idx=near[np.argmin(np.linalg.norm(co[near]-c,axis=1))];w=allw[idx]
 for i in ids:allw[i]=w
for i,w in enumerate(allw):
 for n,v in w.items():groups[n].add([i],v,'REPLACE')
o.parent=rig;mod=o.modifiers.new('Armature','ARMATURE');mod.object=rig
me.materials.clear()
for name in ['LizardBody','LizardHead']:
 m=bpy.data.materials.new(name);m.use_nodes=True;me.materials.append(m)
for f in me.polygons:f.material_index=1 if head[list(f.vertices)].mean()>.5 else 0;f.use_smooth=True
for n,mask in [('head',head),('jaw',jaw)]:
 a=me.attributes.new(n,'BOOLEAN','POINT')
 for i,v in enumerate(mask):a.data[i].value=bool(v)
assert all(v.groups for v in me.vertices);assert max(len(v.groups) for v in me.vertices)<=4
(P/'work/rig_report.json').write_text(json.dumps({'bones':{n:{'head':h.tolist(),'tail':t.tolist(),'parent':p} for n,(h,t,p) in bones.items()},'unweighted':0,'max_influences':max(len(v.groups) for v in me.vertices)},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.63,.67,.65);sc.display.shading.show_cavity=True;sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.25;target=Vector((0,-.05,.47));cam.location=target+Vector((3,-5,1.6));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
for label,changes in [('rest',[]),('stride',[('LThigh',(1,0,0),-.45),('RThigh',(1,0,0),.4),('LShin',(1,0,0),.4)]),('attack',[('Neck1',(1,0,0),.22),('Neck2',(1,0,0),.15),('Jaw',(1,0,0),.18),('LUpperArm',(1,0,0),-.3)]),('twist',[('Spine1',(0,0,1),.25),('Tail3',(0,0,1),.35),('Head',(0,0,1),-.3)])]:
 for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.matrix_basis.identity()
 for n,axis,a in changes:rig.pose.bones[n].rotation_quaternion=Quaternion(rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector(axis),a)
 bpy.context.view_layer.update();sc.render.filepath=str(P/'review'/f'probe_{label}.png');bpy.ops.render.render(write_still=True)
print('RIG COMPLETE',len(bones),len(me.vertices))
