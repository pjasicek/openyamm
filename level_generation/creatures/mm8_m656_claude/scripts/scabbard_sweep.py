import bpy,numpy as np,math,json
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_settled.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;body=bpy.data.objects['Body'];prop=bpy.data.objects['ScabbardMesh'];a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
frames=np.arange(0,109.001,.25);rows=[];angles=[]
for f in frames:
 sc.frame_set(int(f),subframe=float(f%1));o=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=o.to_mesh();tree=BVHTree.FromPolygons([body.matrix_world@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);o.to_mesh_clear()
 b=r.pose.bones['Scabbard'];m=b.matrix.copy();pivot=m.translation;o=prop.evaluated_get(bpy.context.evaluated_depsgraph_get());me=o.to_mesh();co=[prop.matrix_world@v.co for v in me.vertices];polys=[tuple(p.vertices) for p in me.polygons];o.to_mesh_clear()
 def hits(deg):
  R=Matrix.Rotation(math.radians(deg),3,'Z');return len(tree.overlap(BVHTree.FromPolygons([pivot+R@(v-pivot) for v in co],polys)))
 candidates=[d for d in range(-90,91,2) if hits(d)==0]
 angle=min(candidates,key=abs) if candidates else 0
 angles.append(angle);rows.append((m,pivot,tree,co,polys))
 print('SWEEP',float(f),angle,hits(angle),flush=True) if hits(0) else None
# Choose one smooth positive or negative envelope, then validate it before writing any keys.
values=np.array(angles);sign=1 if values.sum()>=0 else -1
for i,(m,c,t,co,polys) in enumerate(rows):
 if not angles[i]:continue
 def clear(d):
  R=Matrix.Rotation(math.radians(d),3,'Z');return not t.overlap(BVHTree.FromPolygons([c+R@(v-c) for v in co],polys))
 options=[d*sign for d in range(0,121,2) if clear(d*sign)]
 if options:values[i]=options[0]
values=np.abs(values);held=np.array([values[max(0,i-8):i+9].max() for i in range(len(values))]);k=np.exp(-.5*(np.arange(-16,17)/6)**2);k/=k.sum();sm=np.maximum(values,np.convolve(np.pad(held,16,mode='edge'),k,mode='valid'))*sign
out=[]
for f,(m,c,t,co,polys),deg in zip(frames,rows,sm):
 sc.frame_set(int(f),subframe=float(f%1))
 R=Matrix.Rotation(math.radians(float(deg)),4,'Z');b=r.pose.bones['Scabbard'];b.matrix=Matrix.Translation(c)@R@Matrix.Translation(-c)@m;out.append((float(f),b.rotation_quaternion.copy()))
for f,q in out:b=r.pose.bones['Scabbard'];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
(P/'review/scabbard_sweep.json').write_text(json.dumps({'max_deg':float(max(abs(sm))),'axis':'world Z; preserves floor clearance','frames':list(map(float,frames)),'angles':list(map(float,sm))},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_settled.blend'))
