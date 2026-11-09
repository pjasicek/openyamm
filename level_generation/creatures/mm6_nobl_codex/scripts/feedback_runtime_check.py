"""Check the shipped cloth at 48 fps, including glTF influence truncation and interpolation."""
import bpy,numpy as np,json
from pathlib import Path
from mathutils.kdtree import KDTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v10.blend'))
o=bpy.data.objects['Body'];pv=np.zeros(len(o.data.vertices),np.int32);o.data.attributes['piece'].data.foreach_get('value',pv)
kd=KDTree(len(o.data.vertices))
for v in o.data.vertices:kd.insert(o.matrix_world@v.co,v.index)
kd.balance()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'export/mm6_nobl_runtime_lod0.glb'))
r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');o=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.parent is r);sc=bpy.context.scene
C=[v.index for v in o.data.vertices if pv[kd.find(o.matrix_world@v.co)[1]]==9]
assert len(C)>=87
result={}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];local=[];world=[]
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.00001,sc.render.fps/48):
  sc.frame_set(int(f),subframe=float(f%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();X=np.array([tuple(o.matrix_world@m.vertices[i].co) for i in C]);ev.to_mesh_clear()
  P=np.array((r.matrix_world@r.pose.bones['B_Pelvis'].matrix).inverted());local.append(X@P[:3,:3].T+P[:3,3]);world.append(X)
 local=np.array(local);world=np.array(world);step=np.linalg.norm(np.diff(local,axis=0),axis=2)
 result[a.name]={'tabard_vertices':len(C),'floor_min_mm':float(world[:,:,2].min()*1000),'max_local_step_mm_at_48fps':float(step.max()*1000)}
 assert result[a.name]['floor_min_mm']>0,(a.name,result[a.name])
 if a.name in ['Standing','Fidget']:assert step.max()<.002,(a.name,step.max())
 if a.name=='Walking':assert step.max()<.005,(a.name,step.max())
 if a.name=='Dead':assert step.max()<1e-7,(a.name,step.max())
 print('RUNTIME_CLOTH',a.name,result[a.name],flush=True)
(p/'review/feedback_20261011/runtime_cloth_check.json').write_text(json.dumps(result,indent=1))
