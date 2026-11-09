"""Compare every exported vertex with its fitted native source at 48 Hz."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
def coords(objects):
 result=[]
 for o in objects:
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();result.extend([tuple(o.matrix_world@v.co) for v in m.vertices]);e.to_mesh_clear()
 return np.array(result)
def load_native():
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_master.blend'));r=bpy.data.objects['Rig'];return r,[bpy.data.objects[n] for n in ['Body','AxeMesh']]
def bind(r,objects):
 a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
 bpy.context.view_layer.update();return coords(objects)
r,objects=load_native();native_bind=bind(r,objects);tree=KDTree(len(native_bind))
for i,p in enumerate(native_bind):tree.insert(p,i)
tree.balance();reference={};times={}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;fps=sc.render.fps/sc.render.fps_base;tt=np.arange(0,float(a.frame_range[1])/fps+1e-6,1/48);values=[]
 for t in tt:
  f=t*fps;sc.frame_set(int(f),subframe=f%1);values.append(coords(objects))
 reference[a.name]=np.asarray(values,dtype=np.float32);times[a.name]=tt
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_min1_runtime_lod0.glb'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.find_armature()==r];points=bind(r,objects);matches=[tree.find(tuple(p)) for p in points];indices=np.array([x[1] for x in matches]);bind_error=max(x[2] for x in matches);assert bind_error<1e-4,bind_error;result={}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;fps=sc.render.fps/sc.render.fps_base;worst=(0,0);rms=[]
 for i,t in enumerate(times[a.name]):
  f=t*fps;sc.frame_set(int(f),subframe=f%1);delta=np.linalg.norm(coords(objects)-reference[a.name][i,indices],axis=1);k=int(delta.argmax());value=float(delta[k])
  if value>worst[0]:worst=(value,float(t))
  rms.append(float(np.sqrt(np.mean(delta**2))))
 result[a.name]={'max_vertex_error_mm':worst[0]*1000,'worst_time_seconds':worst[1],'max_rms_mm':max(rms)*1000,'pass':worst[0]<.001}
 print('EXPORT POSE',a.name,result[a.name],flush=True)
report={'method':'48 Hz actual 8-influence GLB vs native source; duplicated UV seam vertices matched in the shared Standing pose (the importer rebuilds its own rest frame).','standing_match_error_mm':bind_error*1000,'clips':result,'pass':all(v['pass'] for v in result.values())};(P/'review/round1/export_pose_gate.json').write_text(json.dumps(report,indent=2));assert report['pass']
