"""Attach ragged garments to the underlying skin, retain the accepted motion and fit floor contact."""
from pathlib import Path
import bpy,json,math
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/weighted_v1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
co=np.array([v.co[:] for v in me.vertices]);region=np.array([v.value for v in me.attributes['region'].data])
gn=[g.name for g in body.vertex_groups];weights=np.zeros((len(co),len(gn)))
for v in me.vertices:
 for g in v.groups:weights[v.index,g.group]=g.weight
skinfaces=[tuple(f.vertices) for f in me.polygons if all(region[i]==0 for i in f.vertices)]
tree=BVHTree.FromPolygons(co.tolist(),skinfaces,all_triangles=True)
for i in np.where(np.isin(region,[1,2]))[0]:
 hit,_,fi,_=tree.find_nearest(Vector(co[i]));ids=skinfaces[fi]
 bary=barycentric_transform(hit,*[Vector(co[v]) for v in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
 bary=np.clip(np.array(bary),0,1);bary/=bary.sum();weights[i]=bary@weights[list(ids)]
for i in np.where(np.isin(region,[4,5,6]))[0]:
 weights[i]=0;weights[i,gn.index('B_Pelvis' if region[i]==6 else 'B_Head')]=1
for v in me.vertices:
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 w=weights[v.index];idx=np.argsort(w)[-8:];idx=idx[w[idx]>1e-5];w=w[idx];w/=w.sum()
 for gi,value in zip(idx,w):body.vertex_groups[int(gi)].add([v.index],float(value),'REPLACE')
# Preserve the donor's full pose and timing; only translate vertically to fit this body's soles.
report={}
for name in ['Standing','Walking','Fidget','Hit','Death','Dead']:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 locations=[];shifts=[]
 for f in range(int(act.frame_range[1])+1):
  scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
  floor=min(v.co.z for v in m.vertices);ev.to_mesh_clear();dz=.003-floor
  pb=rig.pose.bones['B_Pelvis'];mat=pb.matrix.copy();mat.translation.z+=dz;pb.matrix=mat
  locations.append(pb.location.copy());shifts.append(dz)
 for f,loc in enumerate(locations):
  pb.location=loc;pb.keyframe_insert('location',frame=f)
 report[name]={'seconds':act.frame_range[1]/30,'floor_shift_m':[min(shifts),max(shifts)]}
 for layer in act.layers:
  for strip in layer.strips:
   bag=strip.channelbag(act.slots[0])
   if bag:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_fitted.blend'))
(P/'work/motion_fit.json').write_text(json.dumps(report,indent=2)+'\n')
assert len(rig.data.bones)==56
print('MOTION_FIT',report)
