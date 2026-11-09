import bpy,bmesh,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_twist.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();me=body.data;pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([tuple(v.co)for v in me.vertices]);ids=np.where(pv==2)[0];faces=[tuple(f.vertices)for f in me.polygons if pv[f.vertices[0]]==2];tree=BVHTree.FromPolygons(co.tolist(),faces)
# Waist-anchored complete skirt: sixteen four-link chains, weighted continuously around the circle.
chains=[];zs=[.84,.715,.59,.465,.34]
for i in range(16):
 a=2*math.pi*i/16;d=Vector((math.sin(a),math.cos(a),0));pts=[]
 for z in zs:
  o=Vector((0,.015,z));loc,n,fi,dist=tree.ray_cast(o,d,.6)
  if loc is None:
   loc,n,fi,dist=tree.ray_cast(o+Vector((0,0,.025)),d,.6)
   if loc is not None:loc.z=z
  assert loc is not None,(i,z)
  pts.append(list(loc))
 chains.append({'deg':i*22.5,'pts':pts,'bones':[f'Cloak_{i}_{k}'for k in range(4)]})
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for c in chains:
 par=rig.data.edit_bones['B_Pelvis']
 for k,n in enumerate(c['bones']):
  b=rig.data.edit_bones.new(n);b.head=c['pts'][k];b.tail=c['pts'][k+1];b.parent=par;b.use_connect=k>0;par=b
bpy.ops.object.mode_set(mode='OBJECT')
for c in chains:
 for n in c['bones']:body.vertex_groups.new(name=n)
def smooth(x):x=min(1,max(0,x));return x*x*(3-2*x)
def cw(c,z):
 t=max(0,min(3.999,(zs[0]-z)/(zs[0]-zs[-1])*4));k=int(t);r=t-k;w={c['bones'][k]:1}
 if r<.4 and k>0:w={c['bones'][k-1]:.5*(1-r/.4),c['bones'][k]:.5+.5*r/.4}
 elif r>.6 and k<3:w={c['bones'][k+1]:.5*(r-.6)/.4,c['bones'][k]:1-.5*(r-.6)/.4}
 return w
for i in ids:
 v=me.vertices[int(i)];x,y,z=v.co;t=(math.atan2(x,y-.015)%(2*math.pi))/(2*math.pi)*16;j=int(t);r=t-j;anchor=smooth((z-.79)/.05);w={'B_Pelvis':anchor}
 for c,g in [(chains[j],1-r),(chains[(j+1)%16],r)]:
  for n,val in cw(c,z).items():w[n]=w.get(n,0)+val*g*(1-anchor)
 for e in v.groups[:]:body.vertex_groups[e.group].remove([int(i)])
 total=sum(w.values())
 for n,val in w.items():
  if val>1e-8:body.vertex_groups[n].add([int(i)],val/total,'REPLACE')
scene['merchant_skirt']=json.dumps(chains)
# Preserve the native forward collapse; translate the whole figure so its actual surface contacts the floor.
for name in ['Death','Dead']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];vals=[]
 for f in np.arange(0,a.frame_range[1]+.001,.5):
  scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear();M=rig.pose.bones['B_Pelvis'].matrix.copy();M.translation.z+=.004-low;vals.append((float(f),M))
 for f,M in vals:
  scene.frame_set(int(f),subframe=f%1);rig.pose.bones['B_Pelvis'].matrix=M;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/skirt_v1.blend'))
