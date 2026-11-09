"""Refine the fitted fist against the actual skinned triangles, not just finger centrelines."""
import bpy,sys,json,math,os,runpy
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_weighted.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
act=bpy.data.actions['GripRef'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(8)
G=json.loads((P/'work/grip_pose_initial.json').read_text());rig.animation_data.action=None
for n,q in G['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion(q)
bpy.context.view_layer.update()
H=rig.pose.bones['B_R_Hand'].matrix.copy();C=np.array(H@Vector(G['handle_centre_hand_local']));A=np.array((H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized());radius=.0157
co=np.array([tuple(v.co) for v in me.vertices]);lab=np.array([d.value for d in me.attributes['finger'].data]);bones=list(rig.data.bones);bn=[b.name for b in bones];bi={n:i for i,n in enumerate(bn)}
rest={b.name:b.matrix_local.copy() for b in bones};pose0={pb.name:pb.matrix.copy() for pb in rig.pose.bones};q0={pb.name:pb.rotation_quaternion.copy() for pb in rig.pose.bones}
weights=np.zeros((len(co),len(bn)))
for v in me.vertices:
 for g in v.groups:
  n=body.vertex_groups[g.group].name
  if n in bi:weights[v.index,bi[n]]=g.weight
me.calc_loop_triangles();tri=np.array([list(t.vertices) for t in me.loop_triangles]);ids=np.where((co[:,0]<0)&((lab>0)|(np.linalg.norm(co-np.array(rest['B_R_Hand'].translation),axis=1)<.15)))[0]
tris=tri[np.all(np.isin(tri,ids),axis=1)]
bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[.5,0,.5],[0,.5,.5],[1/3]*3])
Q={n:q.copy() for n,q in q0.items()}
def skin(qs):
 mats={};D=[]
 for b in bones:
  n=b.name
  if n in G['finger_local']:
   parent=b.parent.name;basis=qs[n].to_matrix().to_4x4();m=mats[parent]@rest[parent].inverted()@rest[n]@basis
  else:m=pose0[n]
  mats[n]=m;D.append(np.array(m@rest[n].inverted()))
 v=np.einsum('nj,jab,nb->na',weights,np.array(D),np.c_[co,np.ones(len(co))])[:,:3]
 return v,mats
initial,_=skin(Q)
pts=np.einsum('kj,tjd->tkd',bary,initial[tris]).reshape(-1,3)
# Place the handle inside the actual palm/web tunnel before changing any curls.
u=np.cross(A,[0,0,1]);u/=np.linalg.norm(u);v=np.cross(A,u);C0=C.copy();best=(1e9,None)
for x in np.linspace(-.012,.012,49):
 for y in np.linspace(-.012,.012,49):
  c=C0+x*u+y*v;rel=pts-c;al=rel@A;r=np.linalg.norm(rel-np.outer(al,A),axis=1);r=r[np.abs(al)<.060]
  depth=np.maximum(radius+.0007-r,0);value=2e6*float((depth**2).sum())+300*(x*x+y*y)
  if value<best[0]:best=(value,c)
C=best[1];G['handle_centre_hand_local']=list(H.inverted()@Vector(C));print('HANDLE RELOCATION MM',((C-C0)*1000).tolist(),'cost',best[0],flush=True)
report={}
for finger in [1,2,3,4,0]:
 ch=[f'B_R_Finger{finger}',f'B_R_Finger{finger}1',f'B_R_Finger{finger}2'] if finger else ['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']
 ftris=tris[np.any(np.isin(tris,np.where((lab==finger+1)&(co[:,0]<0))[0]),axis=1)]
 # Axis in the basis frame before its existing local rotation.
 axes=[]
 for n in ch:
  b=rig.data.bones[n];base=pose0[b.parent.name]@rest[b.parent.name].inverted()@rest[n]
  axes.append((base.to_3x3().inverted()@Vector(A)).normalized())
 finger_dir=(pose0[ch[1]].translation-pose0[ch[0]].translation).normalized();palm_normal=Vector(A).cross(finger_dir).normalized()
 base=pose0[rig.data.bones[ch[0]].parent.name]@rest[rig.data.bones[ch[0]].parent.name].inverted()@rest[ch[0]]
 spread=(base.to_3x3().inverted()@palm_normal).normalized()
 start={n:Q[n].copy() for n in ch}
 def evaluate(x,commit=False):
  qs=dict(Q)
  for k,n in enumerate(ch):
   qs[n]=Quaternion(axes[k],math.radians(x[k]))@start[n]
  qs[ch[0]]=Quaternion(spread,math.radians(x[3]))@qs[ch[0]]
  v,m=skin(qs);pts=np.einsum('kj,tjd->tkd',bary,v[ftris]).reshape(-1,3)
  rel=pts-C;al=rel@A;r=np.linalg.norm(rel-np.outer(al,A),axis=1);r=r[np.abs(al)<.064]
  depth=np.maximum(radius+.0007-r,0)
  # Strong collision penalty; keep a light contact band and the original natural curl.
  value=2e6*float((depth**2).sum())+2e4*max(0,float(np.min(r))-radius-.0015)**2+.00001*float(np.sum(np.array(x)**2))
  if commit:return qs,{'minimum_surface_radius_m':float(np.min(r)),'delta_deg':list(map(float,x)),'score':value}
  return value
 x=np.zeros(4);best=evaluate(x)
 for step in [12,6,3,1,.3]:
  for sweep in range(12):
   changed=False
   for j in range(4):
    for sign in [-1,1]:
     y=x.copy();y[j]+=sign*step
     if abs(y[j])>22:continue
     value=evaluate(y)
     if value<best-1e-10:best=value;x=y;changed=True
   if not changed:break
 Q,r=evaluate(x,True);report[str(finger)]=r;print('REFINE',finger,r,flush=True)
for n in G['finger_local']:G['finger_local'][n]=list(Q[n]);rig.pose.bones[n].rotation_quaternion=Q[n]
bpy.context.view_layer.update();G['surface_refinement']=report;G['physical_grip_radius']=radius
(P/'work/grip_pose.json').write_text(json.dumps(G,indent=2));(P/'review/grip_refinement.json').write_text(json.dumps(report,indent=2))
# Render isolated evaluated right hand with its actual grip radius.
import bmesh
v,m=skin(Q);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
for vert in bm.verts:vert.co=Vector(v[vert.index])
bmesh.ops.delete(bm,geom=[x for x in bm.verts if (x.co-Vector(C)).length>.14],context='VERTS')
mesh=bpy.data.meshes.new('Hand');bm.to_mesh(mesh);bm.free();o=bpy.data.objects.new('Hand',mesh);bpy.context.scene.collection.objects.link(o);body.hide_render=True
bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=.20,location=Vector(C));h=bpy.context.object;h.rotation_mode='QUATERNION';h.rotation_quaternion=Vector((0,0,1)).rotation_difference(Vector(A))
mat=bpy.data.materials.new('Handle');mat.diffuse_color=(.4,.2,.07,1);h.data.materials.append(mat)
sc=bpy.context.scene;common.workbench_clay(sc)
for name,d in [('axis',Vector(A)),('palm',palm_normal),('side',Vector(A).cross(palm_normal)),('back',-palm_normal)]:
 cam=common.ortho_camera('cam',Vector(C)+d,(0,0,0),.27);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam;sc.render.resolution_x=sc.render.resolution_y=512;sc.render.filepath=str(P/f'review/grip_refined_{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
sys.argv=['apply_grip.py','--',str(P/'work/rig_weighted.blend'),str(P/'work/rig_grip.blend')];runpy.run_path(str(P/'scripts/apply_grip.py'),run_name='__main__')
