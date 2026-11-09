"""Export the frozen fitted rig with body, head and detailed axe materials."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];T=P/'textures'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_master.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];sc=bpy.context.scene
assert sc.render.fps==240 and sc.render.fps_base==1
KEEP=('Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget')
for a in list(bpy.data.actions):
 if a.name not in KEEP:bpy.data.actions.remove(a)
def pose(n,f):
 a=bpy.data.actions[n];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f-int(f))
def coords(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array([tuple(o.matrix_world@x.co) for x in m.vertices]);e.to_mesh_clear();return v
metrics={'clips':{},'body_triangles':sum(len(p.vertices)-2 for p in b.data.polygons),'axe_triangles':sum(len(p.vertices)-2 for p in ax.data.polygons),'bones':len(r.data.bones)}
for n in KEEP:
 a=bpy.data.actions[n];lo,hi=a.frame_range;bb=[];foot=[]
 for f in np.linspace(lo,hi,max(2,int(hi-lo)+1)):
  pose(n,float(f));v=coords(b);bb.append([v.min(0),v.max(0)]);foot.append([list(r.pose.bones['B_'+s+'_Foot'].head) for s in 'RL'])
 bb=np.array(bb);foot=np.array(foot)
 metrics['clips'][n]={'duration':float((hi-lo)/sc.render.fps),'bounds_min':bb[:,0].min(0).tolist(),'bounds_max':bb[:,1].max(0).tolist(),'foot_forward_range_m':np.ptp(foot[:,:,1],axis=0).tolist()}
pose('Standing',0);v=coords(b);metrics['standing_body_height_m']=float(np.ptp(v[:,2]));metrics['scale']=186.9/metrics['standing_body_height_m'];metrics['run_stride_m']=float(np.mean(metrics['clips']['Walking']['foot_forward_range_m'])*2)
(P/'review/runtime_metrics.json').write_text(json.dumps(metrics,indent=2))
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
sys.path.insert(0,str(P/'scripts'));import round1_materials as M
M.setup(b,ax,directory=P/'textures/round1_rebaked',rebaked=True)
for o in bpy.data.objects:o.select_set(o in [b,ax])
bpy.context.view_layer.objects.active=b;bpy.ops.object.join();b.name=b.data.name='Minotaur'
for n in ['piece','finger','head','orig_co']:
 if n in b.data.attributes:b.data.attributes.remove(b.data.attributes[n])
pose('Standing',0)
for o in bpy.data.objects:o.select_set(o in [r,b])
bpy.context.view_layer.objects.active=r
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_master.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_min1_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
print('RUNTIME_METRICS',json.dumps(metrics))

# Export samples end on a whole frame; publish those exact clip lengths to the viewer.
import struct
raw=(P/'export/mm6_min1_lod0.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n])
for a in doc['animations']:
 duration=max(doc['accessors'][s['input']]['max'][0] for s in a['samplers'])
 assert abs(duration-metrics['clips'][a['name']]['duration'])<=1/sc.render.fps+1e-5
 metrics['clips'][a['name']]['duration']=duration
(P/'review/runtime_metrics.json').write_text(json.dumps(metrics,indent=2))
