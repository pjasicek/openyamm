"""Rigid skeletal pieces on fitted humanoid-set frames; own project only."""
import bpy, bmesh, json, sys, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
import common
SRC=json.loads((P/'work/source_rest.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
def points(o):return np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices])
def ends(n,ref):
 c=points(parts[n]);m=c.mean(0);a=np.linalg.svd(c-m,full_matrices=False)[2][0]
 t=(c-m)@a;v=[m+a*t.min(),m+a*t.max()]
 return v if np.linalg.norm(v[0]-ref)<np.linalg.norm(v[1]-ref) else v[::-1]
def center(n):return points(parts[n]).mean(0)
# The original skull failed inspection; its stretched scraps and floating speck are removed too.
drop=[0,6,12,19,22,29,56,61,63,93,94]
for i in drop:bpy.data.objects.remove(parts.pop(f'P{i:02d}'),do_unlink=True)
bm=bmesh.new();bm.from_mesh(parts['P01'].data)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z>1.46],context='VERTS')
bm.to_mesh(parts['P01'].data);bm.free()
J={'B_Pelvis':Vector((0,.05,.97)),'B_Spine':Vector((0,.06,1.05)),
   'B_Spine1':Vector((0,.065,1.17)),'B_Spine2':Vector((0,.07,1.30)),
   'B_Neck':Vector((0,.075,1.435)),'B_Head':Vector((0,.075,1.535))}
CHAINS={'L':[[50,39,67],[69,52,59,79],[38,64,72],[44,46,85],[45,57,70]],
        'R':[[51,47,66],[71,53,60,81],[37,58,76],[40,48,77],[49,55,75]]}
PALM={'L':[68,73,82,88,86,87,43,36,62,90], 'R':[74,78,80,83,84,89,54,41,65,91]}
BONE={}
def assign(ids,bone):
 for i in ids:
  n=f'P{i:02d}';assert n in parts,n;assert n not in BONE,n;BONE[n]=bone
assign([1,2,11,13,33],'B_Spine2');assign([5,18,24,28,32,34,35,42,92],'B_Pelvis')
FJ={}
for s,sg,hum,fore,fem,shin,boot in [('L',1,10,25,7,20,3),('R',-1,9,23,8,21,4)]:
 shoulder,elbow=ends(f'P{hum:02d}',np.array([sg*.16,.07,1.43]))
 ef,wrist0=ends(f'P{fore:02d}',elbow);elbow=(elbow+ef)/2
 # Wrist from the proximal carpal cluster, independent of the forearm endpoint.
 wrist=np.mean([center(f'P{i:02d}') for i in PALM[s][:2]],axis=0)
 J[f'B_{s}_Clavicle']=Vector((sg*.04,.075,1.415))
 for n,x in [('UpperArm',shoulder),('Forearm',elbow),('Hand',wrist)]:J[f'B_{s}_{n}']=Vector(x)
 hip,knee=ends(f'P{fem:02d}',np.array([sg*.10,.04,.97]))
 sk,ankle=ends(f'P{shin:02d}',knee);knee=(knee+sk)/2
 ankle=np.array([ankle[0],.055,.18]);toe=np.array([ankle[0],-.105,.055])
 for n,x in [('Thigh',hip),('Calf',knee),('Foot',ankle),('Toe0',toe)]:J[f'B_{s}_{n}']=Vector(x)
 assign([hum],f'B_{s}_UpperArm');assign([fore,14 if s=='L' else 15],f'B_{s}_Forearm')
 assign([fem],f'B_{s}_Thigh');assign([shin,31 if s=='L' else 30],f'B_{s}_Calf')
 assign([boot],f'B_{s}_Foot');assign([16,27] if s=='L' else [17,26],f'B_{s}_UpperArm')
 assign(PALM[s],f'B_{s}_Hand')
 FJ[s]={}
 for i,chain in enumerate(CHAINS[s]):
  names=[f'B_{s}_Finger{i}',f'B_{s}_Finger{i}1',f'B_{s}_Finger{i}2']
  if s=='R' and i==0:names=['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']
  ref=wrist
  for k,n in enumerate(names):
   a,b=ends(f'P{chain[k]:02d}',ref);J[n]=Vector(a);ref=b
   FJ[s][n]=list(a);assign([chain[k]],n)
  if len(chain)>3:
   assign(chain[3:],names[-1]);ref=ends(f'P{chain[-1]:02d}',ref)[1]
  FJ[s][names[-1]+'_tip']=list(ref)
assert set(parts)==set(BONE),set(parts)-set(BONE)
# Install the head-only model at the native neck/crown proportions.
with bpy.data.libraries.load(str(P/'work/skull_v1_parts.blend'),link=False) as (a,b):
 b.objects=[n for n in a.objects if n.startswith('P')]
HEAD=[];CROWN=[]
for o in b.objects:
 bpy.context.scene.collection.objects.link(o)
 idx=int(o.name.split('.')[0][1:]);o.name=f'H{idx:02d}'
 for v in o.data.vertices:v.co=Vector((v.co.x*.211111, v.co.y*.211111+.04, v.co.z*.211111+1.42))
 # The cervical pieces follow the neck; the skull and crown remain rigid on the head.
 cervical=idx in list(range(4,27))
 bone='B_Neck' if cervical else 'B_Head'
 parts[o.name]=o;BONE[o.name]=bone;HEAD.append(o.name)
 if idx in [1,36,44,45,50,55,57,58,59,61,66,67,68,69,70,71,72,73,74]:CROWN.append(o.name)
# Clone source coordinate frames, using each real segment and a mesh-measured hand basis.
order=[]
def visit(n):
 order.append(n)
 for k,v in SRC.items():
  if v['parent']==n:visit(k)
visit('B_Pelvis');R={};Q={}
for n in order:
 src=SRC[n];rs=Matrix(src['rot']);child=src['child'];par=src['parent']
 if child in J:q=Vector(src['seg']).rotation_difference(J[child]-J[n])
 elif par in Q:q=Q[par].copy()
 else:q=Quaternion()
 if n=='B_Pelvis':q=Quaternion()
 Q[n]=q;R[n]=q.to_matrix()@rs
for s in ['L','R']:
 hn=f'B_{s}_Hand'
 def basis(f,t):
  f=f.normalized();t=(t-f*t.dot(f)).normalized();return Matrix((f,t,f.cross(t))).transposed()
 ownf=J[f'B_{s}_Finger2']-J[hn];ownt=J[f'B_{s}_Finger1']-J[f'B_{s}_Finger4']
 sf=Vector(SRC[f'B_{s}_Finger2']['head'])-Vector(SRC[hn]['head'])
 st=Vector(SRC[f'B_{s}_Finger1']['head'])-Vector(SRC[f'B_{s}_Finger4']['head'])
 q=(basis(ownf,ownt)@basis(sf,st).transposed()).to_quaternion();Q[hn]=q;R[hn]=q.to_matrix()@Matrix(SRC[hn]['rot'])
 for n in [n for n in order if n.startswith(f'B_{s}_Finger')]:
  c=SRC[n]['child'];target=J[c] if c in J else Vector(FJ[s][n+'_tip'])
  srcseg=Vector(SRC[n]['seg']) if c else Vector(SRC[n]['head'])-Vector(SRC[SRC[n]['parent']]['head'])
  fq=(q@srcseg).rotation_difference(target-J[n])@q
  Q[n]=fq;R[n]=fq.to_matrix()@Matrix(SRC[n]['rot'])
ad=bpy.data.armatures.new('Rig');rig=bpy.data.objects.new('Rig',ad);bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n in order:
 e=ad.edit_bones.new(n);e.head=J[n];c=SRC[n]['child'];ln=(J[c]-J[n]).length if c in J else .025
 e.tail=e.head+R[n].col[1]*max(.015,ln);e.align_roll(R[n].col[2])
for n in order:
 if SRC[n]['parent'] in ad.edit_bones:ad.edit_bones[n].parent=ad.edit_bones[SRC[n]['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
err=max(math.degrees(ad.bones[n].matrix_local.to_quaternion().rotation_difference(R[n].to_quaternion()).angle) for n in order)
assert err<.1,err
# Every bone/equipment component keeps rigid weights; no distance-based finger weight transfer.
for o in bpy.context.scene.objects:o.select_set(False)
for n,o in parts.items():
 o.data.materials.clear();mat=bpy.data.materials.get('LichHead' if n in HEAD else 'Lich')
 if mat is None:mat=bpy.data.materials.new('LichHead' if n in HEAD else 'Lich');mat.diffuse_color=(.7,.67,.59,1)
 o.data.materials.append(mat)
 o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(n[1:])+(100 if n in HEAD else 0)]*len(o.data.vertices))
 o.vertex_groups.clear();o.vertex_groups.new(name=BONE[n]).add(list(range(len(o.data.vertices))),1,'REPLACE')
 if n in CROWN:o.vertex_groups.new(name='CrownGeometry').add(list(range(len(o.data.vertices))),1,'REPLACE')
 o.select_set(True)
 for f in o.data.polygons:f.use_smooth=True
bpy.context.view_layer.objects.active=parts['P01'];bpy.ops.object.join();body=bpy.context.object;body.name='Body'
body.parent=rig;mod=body.modifiers.new('Armature','ARMATURE');mod.object=rig
scene=bpy.context.scene;scene.render.fps=30
scene['rig_offsets']=json.dumps({n:{'q':list(Q[n]),'R_src':SRC[n]['rot']} for n in order})
scene['piece_bones']=json.dumps(BONE);scene['rig_method']='rigid component weights; source frames; mesh knuckle hand frames'
(P/'work/joints_final.json').write_text(json.dumps({'joints':{n:list(v) for n,v in J.items()},'frame_error_degrees':err},indent=2))
(P/'work/finger_joints.json').write_text(json.dumps(FJ,indent=2))
(P/'work/piece_bones.json').write_text(json.dumps(BONE,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
common.workbench_clay(scene);common.render_views(str(P/'review/rig_bind'),.9,2.0,views=('front','left','three_quarter'),resolution=(600,900))
print('RIG',len(order),'frame_error',err,'triangles',sum(len(f.vertices)-2 for f in body.data.polygons))
