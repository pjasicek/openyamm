"""Compare actual exported, reimported surfaces to the retained animated master across all clips."""
import bpy,json,numpy as np,math
from pathlib import Path
from mathutils.kdtree import KDTree
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/anatomy_20261006_r5');bpy.ops.wm.open_mainfile(filepath=str(OUT/'goblin_anatomy_r5.blend'))
scene=bpy.context.scene;source_arm=bpy.data.objects['Goblin_Rig'];names=['Goblin_Body','Goblin_Sword'];source={n:bpy.data.objects[n] for n in names};fps=scene.render.fps
clips=['Standing','Walk','Attack','Hit','Death','Corpse','Fidget','Meshy_Walk','Meshy_Run'];times={c:np.linspace(0,(bpy.data.actions[c].frame_range[1]-bpy.data.actions[c].frame_range[0])/fps,61 if c=='Death' else 25) for c in clips};baseline={}
def surface(o):
 m=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;a=np.array([tuple(o.matrix_world@v.co) for v in m.vertices],dtype=np.float32);return a
source_bone_names=set(source_arm.data.bones.keys())
source_weights={n:[{o.vertex_groups[g.group].name:g.weight for g in v.groups if o.vertex_groups[g.group].name in source_bone_names and g.weight>1e-6} for v in o.data.vertices] for n,o in source.items()}
rest={n:np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]) for n,o in source.items()}
for c in clips:
 a=bpy.data.actions[c];source_arm.animation_data.action=a;source_arm.animation_data.action_slot=a.slots[0];baseline[c]={n:[] for n in names}
 for t in times[c]:
  frame=1+t*fps;scene.frame_set(int(frame),subframe=float(frame-int(frame)))
  for n,o in source.items():baseline[c][n].append(surface(o))
print('Captured revised head surfaces and unchanged dependencies for all nine clips.',flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=fps;bpy.ops.import_scene.gltf(filepath=str(OUT/'goblin_anatomy_r5.glb'),merge_vertices=False)
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');scene=bpy.context.scene;arm.data.pose_position='REST';bpy.context.view_layer.update();mapping={};bind_errors={};imported={}
for n in names:
 o=bpy.data.objects[n];imported[n]=o;k=KDTree(len(rest[n]))
 for i,v in enumerate(rest[n]):k.insert(v,i)
 k.balance();indices=[];distances=[]
 for vertex,v in zip(o.data.vertices,surface(o)):
  _,idx,distance=k.find(v)
  weights={o.vertex_groups[g.group].name:g.weight for g in vertex.groups if o.vertex_groups[g.group].name in source_bone_names and g.weight>1e-6}
  candidates=[candidate[1] for candidate in k.find_range(v,2e-6)]
  def weight_error(i):return sum(abs(weights.get(name,0)-source_weights[n][i].get(name,0)) for name in weights.keys()|source_weights[n][i].keys())
  if candidates:idx=min(candidates,key=weight_error)
  assert weight_error(idx)<.0003,(n,vertex.index,weights,source_weights[n][idx],'export weight mismatch')
  indices.append(idx);distances.append(distance)
 mapping[n]=np.array(indices);bind_errors[n]=max(distances);assert max(distances)<2e-6,(n,max(distances),'bind mismatch')
arm.data.pose_position='POSE';report={}
for c in clips:
 actions=[a for a in bpy.data.actions if a.name==c];assert len(actions)==1,(c,[a.name for a in bpy.data.actions]);a=actions[0];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];maximum={n:0 for n in names};ground=1.
 for i,t in enumerate(times[c]):
  frame=a.frame_range[0]+t*fps;scene.frame_set(int(frame),subframe=float(frame-int(frame)))
  for n,o in imported.items():
   v=surface(o);error=float(np.linalg.norm(v-baseline[c][n][i][mapping[n]],axis=1).max());maximum[n]=max(maximum[n],error);ground=min(ground,float(v[:,2].min()));assert np.isfinite(v).all()
 assert max(maximum.values())<.001,(c,maximum,'motion export mismatch')
 source_ground=min(float(v[:,2].min()) for samples in baseline[c].values() for v in samples)
 assert abs(ground-source_ground)<.001,(c,ground,source_ground,'export contact regression')
 if not c.startswith('Meshy_'):assert ground>-.008,(c,ground,'native export floor penetration')
 report[c]={'samples':len(times[c]),'maximum_surface_difference_m':maximum,'minimum_world_ground_z_m':ground,'source_minimum_world_ground_z_m':source_ground,'contact_status':'needs_review_existing_stock_gait' if ground<-.008 else 'within_tolerance'};print(c,report[c],flush=True)
(OUT/'review/export_reimport_checks.json').write_text(json.dumps({'status':'pass_export_fidelity','actual_glb':'goblin_anatomy_r5.glb','bind_surface_maximum_errors_m':bind_errors,'clips':report,'tolerance_m':.001,'scope':'Actual glTF skin/animation evaluated after isolated reimport, not only JSON inspection.'},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'reimported_anatomy.blend'))
