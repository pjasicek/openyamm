"""Protected, measured reduction candidates. Geometry only; accepted action samples are never authored here."""
import bpy,bmesh,sys,json,math,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
OUT=P/'review/reduction';WORK=P/'work/reduction';WORK.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
CALIBRATION={}
ROLES=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']

def activate(name,time=0):
 rig=bpy.data.objects['Rig'];a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=time*bpy.context.scene.render.fps;bpy.context.scene.frame_set(int(f),subframe=f%1)
def reset():
 rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
def triangles(o):return sum(len(f.vertices)-2 for f in o.data.polygons)
def cleanup():
 for o in list(bpy.data.objects):
  if o.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(o,do_unlink=True)
def protect(obj,kind):
 reset();me=obj.data
 # Keep exported UV splits as topology boundaries so collapse cannot interpolate across unrelated charts.
 me.update()
 co=np.array([tuple(obj.matrix_world@v.co)for v in me.vertices]);names={g.index:g.name for g in obj.vertex_groups};protected=np.zeros(len(co),bool);reasons={};priority=np.zeros(len(co))
 if kind=='body':
  pv=np.array([x.value for x in me.attributes['piece'].data]);face=(pv==0)&(co[:,1]<.025)&(co[:,2]>1.395)
  hands=np.array([sum(g.weight for g in v.groups if 'Hand'in names[g.group]or 'Finger'in names[g.group])>.1 for v in me.vertices]);soles=co[:,2]<.016
  loops=np.zeros(len(co),bool)
  for sd in 'LR':
   for n,radius in [('UpperArm',.045),('Forearm',.035),('Thigh',.035),('Calf',.030)]:
    J=np.array(bpy.data.objects['Rig'].data.bones[f'B_{sd}_{n}'].head_local);loops|=np.linalg.norm(co-J,axis=1)<radius
  loops|=(pv==1)
  for label,m in [('face',face),('hands_fingers_grip',hands),('deformation_loops',loops),('sole_contact',soles)]:protected|=m;reasons[label]=int(m.sum())
 else:
  # The wrist-fixed grip surface is never simplified; rim/silhouette protection below retains the cutting profile.
  joint=bpy.data.objects['Rig'].data.bones['Knife'];axis=(joint.matrix_local.to_3x3()@Vector((0,0,1))).normalized();height=(co-np.array(joint.head_local))@np.array(axis);m=(height>-.04)&(height<.025);protected|=m;reasons['grip_contact']=int(m.sum())
 priority[protected]=1.0
 # Detect visible contours on a welded analysis copy, keeping UV splits intact in the actual mesh.
 from mathutils.bvhtree import BVHTree
 from mathutils.kdtree import KDTree
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.verts.ensure_lookup_table();bm.normal_update();bm.verts.index_update()
 tree=BVHTree.FromBMesh(bm);contour=[]
 dirs=[Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),0))for i in range(8)]
 for e in bm.edges:
  midpoint=(e.verts[0].co+e.verts[1].co)*.5
  for direction in dirs:
   if len(e.link_faces)==2 and e.link_faces[0].normal.dot(direction)*e.link_faces[1].normal.dot(direction)>=-1e-7:continue
   across=(e.verts[1].co-e.verts[0].co).cross(direction)
   if across.length<1e-8:continue
   across.normalize();hits=[tree.ray_cast(midpoint+across*offset+direction*10,-direction,20)[0] is not None for offset in [-.0015,.0015]]
   if hits[0]!=hits[1]:
    contour.extend(v.co.copy()for v in e.verts);break
 kd=KDTree(len(contour))
 for i,v in enumerate(contour):kd.insert(v,i)
 kd.balance();edge_mask=np.array([kd.find(v.co)[2]<1e-6 for v in me.vertices]);sil=me.attributes.get('_silhouette_protect')or me.attributes.new('_silhouette_protect','BOOLEAN','POINT');sil.data.foreach_set('value',edge_mask.tolist());protected|=edge_mask;priority[edge_mask&(priority==0)]=.02;reasons['eight_view_visible_contours']=int(edge_mask.sum());bm.free()
 group=obj.vertex_groups.get('_reduction_protect')or obj.vertex_groups.new(name='_reduction_protect');group.add(np.flatnonzero(priority==1).tolist(),1,'REPLACE');group.add(np.flatnonzero(priority==.02).tolist(),.02,'REPLACE');reasons['total']=int(protected.sum());reasons['vertices']=len(co)
 return reasons

def reduce(obj,ratio,planar=False,factor=1000):
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 if planar:
  bm=bmesh.new();bm.from_mesh(obj.data);bm.verts.ensure_lookup_table();di=bm.verts.layers.deform.active;gi=obj.vertex_groups['_reduction_protect'].index
  allowed={v for v in bm.verts if v[di].get(gi,0)<.5};edges=[e for e in bm.edges if all(v in allowed for v in e.verts)]
  bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(.25),use_dissolve_boundaries=False,verts=list(allowed),edges=edges,delimit={'NORMAL','MATERIAL','SEAM','SHARP','UV'});bm.to_mesh(obj.data);bm.free()
 mod=obj.modifiers.new('MeasuredCollapse','DECIMATE');mod.decimate_type='COLLAPSE';mod.ratio=ratio;mod.use_collapse_triangulate=True;mod.vertex_group='_reduction_protect';mod.invert_vertex_group=True;mod.vertex_group_factor=factor
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
 # Remove simplification weights from normalization; only actual deform joints belong to the skin.
 gi=obj.vertex_groups['_reduction_protect'].index
 for v in obj.data.vertices:
  weights=[(g.group,g.weight)for g in v.groups if g.group!=gi];weights=sorted(weights,key=lambda t:-t[1])[:8];total=sum(w for _,w in weights);assert total>0
  for g in list(v.groups):
   if g.group!=gi:obj.vertex_groups[g.group].remove([v.index])
  for g,w in weights:obj.vertex_groups[g].add([v.index],w/total,'REPLACE')

