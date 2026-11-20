"""Dense export parity, unit bones, actual surfaces, loop/end states and UV checks."""
from pathlib import Path
import bpy, json, numpy as np, importlib.util
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'delivery/mm6_flying_demon.blend'))
source=bpy.context.scene;source_rig=next(o for o in source.objects if o.type=='ARMATURE')
target=bpy.data.scenes.new('Actual_Flying_GLB_Check');target.render.fps=48;bpy.context.window.scene=target
bpy.ops.import_scene.gltf(filepath=str(P/'delivery/mm6_flying_demon_a.glb'))
target_rig=next(o for o in target.objects if o.type=='ARMATURE')
source_objects={o.name:o for o in source.objects if o.type=='MESH'}
# Blender creates a hidden Icosphere bone-display helper during glTF import.
# Compare only meshes named in the actual GLB, and reject unexplained extras.
import sys
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb
document,_=read_glb(P/'delivery/mm6_flying_demon_a.glb')
mesh_nodes={n['name'] for n in document['nodes'] if 'mesh' in n}
assert mesh_nodes==set(source_objects),(mesh_nodes,set(source_objects))
helpers=[o for o in target.objects if o.type=='MESH' and o.name.split('.')[0] not in mesh_nodes]
assert all(o.name.startswith('Icosphere') and o in {b.custom_shape for b in target_rig.pose.bones} for o in helpers),[(o.name,o.hide_render) for o in helpers]
target_objects={o.name.split('.')[0]:o for o in target.objects if o.type=='MESH' and o.name.split('.')[0] in mesh_nodes}
assert set(source_objects)==set(target_objects),(set(source_objects)-set(target_objects),set(target_objects)-set(source_objects))
CLIPS={'Flight':36,'Attack':36,'Hit':36,'Death':42,'Ash_Remains':6}

def select(scene,clip,frame):
 bpy.context.window.scene=scene
 for o in scene.objects:
  if o.type=='ARMATURE': o.hide_set(False)
  for owner in (o,o.data.shape_keys if o.type=='MESH' else None):
   if owner and owner.animation_data:
    tracks=[t for t in owner.animation_data.nla_tracks if t.name==clip]
    for t in owner.animation_data.nla_tracks: t.mute=True
    owner.animation_data.action=tracks[0].strips[0].action if tracks else None
    if tracks: owner.animation_data.action_slot=tracks[0].strips[0].action_slot
 scene.frame_set(int(frame),subframe=float(frame%1));bpy.context.view_layer.update()
def vertices(obj):
 evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());data=evaluated.to_mesh()
 coords=np.empty(len(data.vertices)*3,np.float32);data.vertices.foreach_get('co',coords)
 evaluated.to_mesh_clear();matrix=np.array(evaluated.matrix_world)
 return coords.reshape(-1,3)@matrix[:3,:3].T+matrix[:3,3]

select(source,'Flight',0);select(target,'Flight',0)
mapping={}
for name,obj in source_objects.items():
 clip,frame=('Death',24) if 'Disintegration' in name else ('Ash_Remains',0) if 'Ash' in name else ('Flight',0)
 select(source,clip,frame);select(target,clip,frame)
 bpy.context.window.scene=source;a=vertices(obj);bpy.context.window.scene=target;b=vertices(target_objects[name])
 # Export seam splits change raw vertex counts; match deformed surface positions.
 tree=KDTree(len(a))
 for i,co in enumerate(a): tree.insert(co,i)
 tree.balance();nearest=[tree.find(co) for co in b];error=max(x[2] for x in nearest)
 assert error<2e-5,(name,'initial surface mismatch',error)
 mapping[name]=np.array([x[1] for x in nearest])
report={'rig_joints':len(source_rig.data.bones),'native_timing':True,'actual_glb_reimport':True,'clips':{}}
loop_start=None
for clip,end in CLIPS.items():
 maximum=0;matrix_error=0;morph_error=0;scale_error=0;min_foot=float('inf');q_steps=[];previous=None
 for frame in np.arange(0,end+.01,.5):
  select(source,clip,float(frame));expected={name:vertices(o) for name,o in source_objects.items()}
  mats={b.name:np.array(b.matrix) for b in source_rig.pose.bones}
  assert all(np.isfinite(v).all() for v in expected.values())
  for b in source_rig.pose.bones:
   assert max(abs(s-1) for s in b.scale)<1e-5,(clip,frame,b.name,'bone scale')
   if b.name!='mixamorig:Hips': assert b.location.length<2e-5,(clip,frame,b.name,'bone translation')
  if clip in ('Flight','Attack','Hit'): min_foot=min(min_foot,float(expected['Flying_Demon_Body'][:,2].min()))
  current={b.name:b.matrix.to_quaternion() for b in source_rig.pose.bones}
  if previous:
   q_steps.extend(min(q.rotation_difference(previous[n]).angle,2*np.pi-q.rotation_difference(previous[n]).angle) for n,q in current.items())
  previous=current
  morph=[k.value for k in source_objects['Flying_Demon_Disintegration'].data.shape_keys.key_blocks][1:]
  scales={n:tuple(source.objects[n].scale) for n in ('Flying_Demon_Visibility','Flying_Demon_Ash','Flying_Demon_Disintegration')}
  select(target,clip,float(frame))
  for name,obj in target_objects.items():
   actual=vertices(obj);maximum=max(maximum,float(np.abs(expected[name][mapping[name]]-actual).max()))
  for name,mat in mats.items(): matrix_error=max(matrix_error,float(np.abs(mat-np.array(target_rig.pose.bones[name].matrix)).max()))
  actual_morph=[k.value for k in target_objects['Flying_Demon_Disintegration'].data.shape_keys.key_blocks][1:]
  morph_error=max(morph_error,float(np.abs(np.array(morph)-actual_morph).max()))
  for name,scale in scales.items():
   obj=next(o for o in target.objects if o.name.split('.')[0]==name);scale_error=max(scale_error,max(abs(a-b) for a,b in zip(scale,obj.scale)))
 assert maximum<3e-5 and matrix_error<3e-5 and morph_error<1e-5 and scale_error<1e-5,(clip,maximum,matrix_error,morph_error,scale_error)
 if clip in ('Flight','Attack','Hit'): assert min_foot>.025,(clip,'airborne foot clearance',min_foot)
 # A half-frame samples glTF interpolation too, rather than testing only exported keys.
 assert max(q_steps,default=0)<np.deg2rad(45),(clip,'rotation flip',max(q_steps))
 report['clips'][clip]={'duration_s':end/48,'half_frame_samples':end*2+1,'maximum_surface_error':maximum,'maximum_bone_matrix_error':matrix_error,
  'maximum_morph_error':morph_error,'maximum_visibility_error':scale_error,'maximum_half_frame_rotation_degrees':float(np.rad2deg(max(q_steps,default=0))),
  'minimum_living_surface_height':min_foot if np.isfinite(min_foot) else None}
 print('PARITY',clip,report['clips'][clip],flush=True)
select(source,'Flight',0);start={b.name:np.array(b.matrix_basis) for b in source_rig.pose.bones}
select(source,'Flight',36);loop_error=max(float(abs(start[b.name]-np.array(b.matrix_basis)).max()) for b in source_rig.pose.bones)
assert loop_error<1e-5,loop_error
report['flight_loop_max_error']=loop_error
select(source,'Death',24);assert source_rig.parent.scale.length==0
select(source,'Death',42);assert max(k.value for k in source_objects['Flying_Demon_Disintegration'].data.shape_keys.key_blocks[1:8])==0
select(source,'Ash_Remains',0);ash=vertices(source_objects['Flying_Demon_Ash'])
select(source,'Ash_Remains',6);assert np.array_equal(ash,vertices(source_objects['Flying_Demon_Ash']))
select(source,'Flight',0);assert source_rig.parent.scale==__import__('mathutils').Vector((1,1,1))
assert source_objects['Flying_Demon_Ash'].scale.length==0 and source_objects['Flying_Demon_Disintegration'].scale.length==0
(P/'review/export_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('All dense export, morph, visibility, held ash and loop checks passed.',flush=True)
