"""Open the delivered project and reimport the actual GLB in a separate background Blender process."""
import bpy
import json
import numpy as np
import struct
from pathlib import Path

stage=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(stage/'mm6_demon_attack.blend'))
source_scene=bpy.data.scenes['MM6_Demon_Attack']
source_rig=source_scene.objects['Demon_Attack_Rig'];source_mesh=source_scene.objects['Demon_Attack_Mesh']
source_actions={t.name:t.strips[0].action for t in source_rig.animation_data.nla_tracks}
source_pose_frame=source_scene.frame_current
for t in source_rig.animation_data.nla_tracks:t.mute=True
raw=(stage/'mm6_demon_attack.glb').read_bytes()
size=struct.unpack_from('<I',raw,12)[0]
document=json.loads(raw[20:20+size])
binary_offset=20+size+8
binary=raw[binary_offset:]
def input_values(accessor_id):
 accessor=document['accessors'][accessor_id];view=document['bufferViews'][accessor['bufferView']]
 offset=view.get('byteOffset',0)+accessor.get('byteOffset',0)
 return np.frombuffer(binary,dtype='<f4',count=accessor['count'],offset=offset)
clip_audit={}
for animation in document['animations']:
 times=[input_values(s['input']) for s in animation['samplers']]
 clip_audit[animation['name']]={'duration_seconds':float(max(t.max() for t in times)),
                              'first_time':float(min(t.min() for t in times)),
                              'samplers':len(times),'largest_time_sample_count':max(len(t) for t in times)}
assert set(clip_audit)=={'Walking','Running','Attack'}
assert abs(clip_audit['Attack']['duration_seconds']-.75)<1e-7
assert len(document['meshes'])==1 and len(document['skins'][0]['joints'])==85
assert not document.get('cameras') and not document.get('textures')
assert not any(n.get('mesh') is not None and n['name']!='Demon_Attack_Mesh' for n in document['nodes'])
check_scene=bpy.data.scenes.new('Attack_Export_Check')
check_scene.render.fps=48
bpy.context.window.scene=check_scene
bpy.ops.import_scene.gltf(filepath=str(stage/'mm6_demon_attack.glb'))
target_rig=next(o for o in check_scene.objects if o.type=='ARMATURE')
target_mesh=next(o for o in check_scene.objects if o.type=='MESH')
target_actions={t.name:t.strips[0].action for t in target_rig.animation_data.nla_tracks}
for t in target_rig.animation_data.nla_tracks:t.mute=True
assert set(target_actions)==set(source_actions)
assert len(target_rig.data.bones)==85
assert len(target_mesh.data.vertices)==7899 and len(target_mesh.data.polygons)==15686
assert [list(f.vertices) for f in target_mesh.data.polygons]==[list(f.vertices) for f in source_mesh.data.polygons]
rest_error=float(np.max(np.abs(np.array([tuple(v.co) for v in target_mesh.data.vertices])-
                              np.array([tuple(v.co) for v in source_mesh.data.vertices]))))
assert rest_error<1e-5
def evaluate(scene,rig,mesh,action,time):
 bpy.context.window.scene=scene
 rig.hide_set(False)
 rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 scene.frame_set(int(time),subframe=float(time%1))
 evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());temporary=evaluated.to_mesh()
 coordinates=np.array([tuple(evaluated.matrix_world@v.co) for v in temporary.vertices])
 evaluated.to_mesh_clear()
 return coordinates
report={'actual_glb_reimport':True,'clips':clip_audit,'rest_coordinate_maximum_error':rest_error,
        'triangle_indices_match':True,'bone_count':85,'pose_checks':{}}
for clip,end,step in [('Attack',36,.25),('Walking',50,.5),('Running',32,.5)]:
 maximum=0;count=0
 for time in np.arange(0,end+.01,step):
  expected=evaluate(source_scene,source_rig,source_mesh,source_actions[clip],float(time))
  actual=evaluate(check_scene,target_rig,target_mesh,target_actions[clip],float(time))
  error=float(np.max(np.abs(expected-actual)))
  assert error<1e-5,(clip,float(time),error)
  maximum=max(maximum,error);count+=1
 report['pose_checks'][clip]={'sampled_times':count,'maximum_mesh_coordinate_error':maximum}
bpy.context.window.scene=source_scene
source_rig.animation_data.action=source_actions['Attack']
source_rig.animation_data.action_slot=source_actions['Attack'].slots[0]
source_scene.frame_set(source_pose_frame)
(stage/'export_roundtrip_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
