"""Sweep the actual exported mesh at 48 Hz, using the authored anatomical regions."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_settled.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];source=np.array([(body.matrix_world@v.co)[:] for v in body.data.vertices]);parts=np.array([a.value for a in body.data.attributes['piece'].data]);jaw=rig.data.bones['B_Head'].head_local.z-.02
tree=kdtree.KDTree(len(source))
for i,p in enumerate(source):tree.insert(Vector(p),i)
tree.balance()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m420_prepared.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['PirateMage'];sc=bpy.context.scene
names={g.index:g.name for g in body.vertex_groups};dom=[names[max(v.groups,key=lambda e:e.weight).group] for v in body.data.vertices];pc=[];rest=[]
for i,v in enumerate(body.data.vertices):
 p=body.matrix_world@v.co;rest.append(p[:])
 if dom[i]=='Staff':pc.append(-2);continue
 _,j,d=tree.find(p);assert d<1e-5,d;pc.append(int(parts[j]))
rest=np.array(rest);pc=np.array(pc)
bodyfaces=[tuple(p.vertices) for p in body.data.polygons if all(pc[i] not in [-2,5,11,14] for i in p.vertices)];stafffaces=[tuple(p.vertices) for p in body.data.polygons if all(pc[i]==-2 for i in p.vertices)]
headfaces=[tuple(p.vertices) for p in body.data.polygons if all(pc[i]==1 and rest[i,2]>jaw for i in p.vertices)]
shoulderfaces=[tuple(p.vertices) for p in body.data.polygons if all(pc[i]==0 and abs(rest[i,0])>.12 and rest[i,2]>1.2 for i in p.vertices)]
report={};dense='--cast-only' in sys.argv
for act in bpy.data.actions:
 if dense and act.name not in ['Attack','Cast']:continue
 rig.animation_data.action=None
 for bone in rig.pose.bones:bone.matrix_basis.identity()
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];low=10;stafflow=10;contacts={};heads={}
 for f in sorted(set([float(act.frame_range[1]),*np.arange(0,float(act.frame_range[1])+.001,.25 if dense else .625)])):
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=[body.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();z=np.array([v.z for v in co]);low=min(low,float(z.min()));stafflow=min(stafflow,float(z[pc==-2].min()))
  n=len(BVHTree.FromPolygons(co,bodyfaces).overlap(BVHTree.FromPolygons(co,stafffaces)))
  h=len(BVHTree.FromPolygons(co,headfaces).overlap(BVHTree.FromPolygons(co,shoulderfaces)))
  if n:contacts[str(f)]=n
  if h:heads[str(f)]=h
 report[act.name]={'floor_min_m':low,'staff_floor_min_m':stafflow,'staff_body_intersections':contacts,'head_shoulder_intersections':heads}
 print('EXPORT_PHYSICS',act.name,report[act.name],flush=True)
(P/('review/dual_cast/physics120.json' if dense else 'review/export_physics.json')).write_text(json.dumps(report,indent=2)+'\n')
assert all(v['floor_min_m']>-.005 and not v['staff_body_intersections'] and not v['head_shoulder_intersections'] for v in report.values())
