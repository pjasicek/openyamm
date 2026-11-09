import bpy,sys,json,math,numpy as np,runpy
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
sys.argv=['g5_hand_stretch.py','--',str(P/'work/master_settled.blend'),'Standing','Walking','Running','Attack','Hit','Death','Fidget'];runpy.run_path(str(P/'scripts/g5_hand_stretch.py'),run_name='__main__')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m656_prepared.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['Mercenary'];sc=bpy.context.scene
names={g.index:g.name for g in body.vertex_groups};dom=[names[max(v.groups,key=lambda e:e.weight).group] for v in body.data.vertices]
props={n:np.array([x==n for x in dom]) for n in ['Sword','Scabbard']};polys=[tuple(f.vertices) for f in body.data.polygons if all(dom[v] not in props for v in f.vertices)]
rest=rig.data.bones['Scabbard'].matrix_local.inverted();scabbard_ids=[i for i,v in enumerate(body.data.vertices) if props['Scabbard'][i] and (rest@v.co).y<-.08]
sp=[tuple(p.vertices) for p in body.data.polygons if all(dom[v]=='Scabbard' for v in p.vertices)]
report={}
for act in bpy.data.actions:
 rig.animation_data.action=None
 for bone in rig.pose.bones:bone.matrix_basis.identity()
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[];worst=(0.,0.);intersections=(0,0.)
 for f in np.arange(0,float(act.frame_range[1])+.001,.625):
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[body.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();z=np.array([v.z for v in co]);rows.append([float(f),float(z.min()),*[float(z[mask].min()) for mask in props.values()]])
  tree=BVHTree.FromPolygons(co,polys)
  intersections=max(intersections,(len(tree.overlap(BVHTree.FromPolygons(co,sp))),float(f)))
  for i in scabbard_ids:
   hit,norm,face,distance=tree.find_nearest(co[i],.1)
   if hit is None:continue
   v=co[i]-hit
   if v.dot(norm)<0 and v.length>1e-6 and (-v).normalized().angle(norm)<math.radians(45) and distance>worst[0]:worst=(distance,float(f))
 a=np.array(rows);report[act.name]={'minimum_floor_cm':float(a[:,1].min()*100),'sword_min_cm':float(a[:,2].min()*100),'scabbard_min_cm':float(a[:,3].min()*100),'scabbard_backface_proximity_cm':worst[0]*100,'contact_frame':worst[1],'triangle_intersections':intersections[0],'intersection_frame':intersections[1]}
 print('EXPORTED_PHYSICS',act.name,report[act.name],flush=True)
 assert a[:,1].min()>-.005
(P/'review/export_physics.json').write_text(json.dumps(report,indent=2)+'\n')
