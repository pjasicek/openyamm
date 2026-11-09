import bpy,json,math,bmesh
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/clean_v1.blend'));o=bpy.data.objects['Body'];me=o.data;co=np.array([v.co[:] for v in me.vertices]);parts=np.array([v.value for v in me.attributes['part'].data]);bones={}
def chain(names,pts,parent):
 for i,n in enumerate(names):bones[n]=(np.array(pts[i],float),np.array(pts[i+1],float),names[i-1] if i else parent)
chain(['Root'],[(0,-.32,.49),(0,-.32,.65)],None)
chain(['Spine1','Spine2'],[(0,-.32,.49),(0,-.60,.56),(0,-.83,.65)],'Root')
chain(['Neck1','Neck2','Neck3'],[(0,-.83,.65),(0,-1.00,.80),(0,-1.14,.93),(0,-1.29,.96)],'Spine2')
chain(['Head'],[(0,-1.29,.96),(0,-1.5,.94)],'Neck3')
chain(['Jaw'],[(0,-1.37,.91),(0,-1.52,.84)],'Head')
pts=[(0,-.32,.49)]
for y in np.linspace(-.15,.84,9):
 a=co[(abs(co[:,1]-y)<.05)&(abs(co[:,0])<.085)];pts.append((0,y,float(np.quantile(a[:,2],.40))))
chain([f'Tail{i}' for i in range(1,10)],pts,'Root')
for side,sg in [('L',1),('R',-1)]:
 chain([side+'Wing0',side+'Wing1',side+'Wing2'],[(sg*.15,-.72,.76),(sg*.53,-.64,1.12),(sg*.99,-.63,1.37),(sg*1.48,-.67,1.52)],'Spine2')
 chain([side+'ForeUpper',side+'ForeLower',side+'ForeFoot'],[(sg*.15,-.84,.64),(sg*.22,-.80,.42),(sg*.22,-1.00,.34),(sg*.23,-1.04,.27)],'Spine2')
 chain([side+'HindUpper',side+'HindLower',side+'HindFoot'],[(sg*.13,-.32,.49),(sg*.20,-.27,.27),(sg*.21,-.14,.16),(sg*.22,-.19,.025)],'Root')
arm=bpy.data.armatures.new('Rig');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n,(h,t,p) in bones.items():
 b=arm.edit_bones.new(n);b.head=h;b.tail=t;b.align_roll(Vector((0,0,1)));b.parent=arm.edit_bones.get(p) if p else None
b=arm.edit_bones.new('Socket_Mouth');b.head=(0,-1.55,.90);b.tail=(0,-1.60,.90);b.parent=arm.edit_bones['Head'];bpy.ops.object.mode_set(mode='OBJECT')
groups={n:o.vertex_groups.new(name=n) for n in bones}
def weight(p,names):
 ds=[]
 for n in names:
  h,t,_=bones[n];d=t-h;u=np.clip(np.dot(p-h,d)/np.dot(d,d),0,1);ds.append(np.linalg.norm(p-h-u*d))
 ds=np.array(ds);ii=np.argsort(ds)[:4];w=np.exp(-((ds[ii]-ds[ii[0]])/.065)**2);w[w<.02]=0;w/=w.sum();return {names[i]:float(v) for i,v in zip(ii,w) if v>0}
wing=(abs(co[:,0])>.22)&(co[:,2]>.76)&(co[:,1]>-.96);head=(co[:,1]<-1.24)&(co[:,2]>.78)&(~wing);jaw=head&(co[:,1]<-1.38)&(co[:,2]<.895)
body=['Spine1','Spine2','Neck1','Neck2','Neck3','Head']+[f'Tail{i}' for i in range(1,10)]
for i,p in enumerate(co):
 side='L' if p[0]>=0 else 'R'
 if wing[i]:
  names=['Spine2',side+'Wing0',side+'Wing1',side+'Wing2'];stations=[.15,.42,.88,1.42];w={n:float(np.interp(abs(p[0]),stations,np.eye(4)[k])) for k,n in enumerate(names)}
 elif head[i]:w={'Jaw' if jaw[i] else 'Head':1.}
 elif p[2]<.64 and p[1]<-.69 and abs(p[0])>.10:
  w={side+'ForeFoot':1.} if p[2]<.335 else weight(p,[side+'ForeUpper',side+'ForeLower',side+'ForeFoot','Spine2'])
 elif p[2]<.55 and -.47<p[1]<-.08 and abs(p[0])>.11:
  w={side+'HindFoot':1.} if p[2]<.16 else weight(p,[side+'HindUpper',side+'HindLower',side+'HindFoot','Spine1'])
 else:w=weight(p,body)
 total=sum(w.values());assert total>0
 for n,v in w.items():
  if v>0:groups[n].add([i],v/total,'REPLACE')
o.parent=rig;mod=o.modifiers.new('Armature','ARMATURE');mod.object=rig
me.materials.clear()
for name in ['DragonBody','DragonHead','DragonWings']:
 m=bpy.data.materials.new(name);m.use_nodes=True;me.materials.append(m)
for f in me.polygons:
 ids=list(f.vertices);f.material_index=2 if wing[ids].mean()>.5 else 1 if head[ids].mean()>.5 else 0
for name,values in [('wing',wing),('head',head),('jaw',jaw)]:
 a=me.attributes.new(name,'BOOLEAN','POINT')
 for i,v in enumerate(values):a.data[i].value=bool(v)
assert all(v.groups for v in me.vertices);assert max(len(v.groups) for v in me.vertices)<=4
(P/'work/rig_report.json').write_text(json.dumps({'bones':{n:{'head':h.tolist(),'tail':t.tolist(),'parent':p} for n,(h,t,p) in bones.items()},'unweighted':0,'max_influences':max(len(v.groups) for v in me.vertices)},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
# Export a rest rig before animation; deformation probes are rendered from this same checkpoint.
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.64,.68,.65);sc.display.shading.show_cavity=True;sc.render.resolution_x=1200;sc.render.resolution_y=900;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=3.6;target=Vector((0,-.45,.75));cam.location=target+Vector((4,-6,2));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
for label,changes in [('rest',[]),('downstroke',[(s+'Wing0',(0,1,0),sg*.7) for s,sg in [('L',1),('R',-1)]]),('attack',[('Neck1',(1,0,0),.3),('Neck2',(1,0,0),.2),('Jaw',(1,0,0),.3)]),('recoil',[('Root',(1,0,0),-.25),('Neck1',(1,0,0),-.2),('Tail3',(1,0,0),.25)])]:
 for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.matrix_basis.identity()
 for n,axis,angle in changes:rig.pose.bones[n].rotation_quaternion=Quaternion(rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector(axis),angle)
 bpy.context.view_layer.update();sc.render.filepath=str(P/'review'/('probe_'+label+'.png'));bpy.ops.render.render(write_still=True)
print('RIGGED',len(bones),'bones',len(me.vertices),'vertices')
