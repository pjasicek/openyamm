"""Audit runtime animation seams and floor placement on the GLB played by the viewer."""
import bpy,sys,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p/'export/mm6_nobl_runtime_lod0.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');b=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.parent is r);sc=bpy.context.scene
def vertices(frame):
 sc.frame_set(int(frame),subframe=frame%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
 a=np.array([tuple(b.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return a
report={}
for name in ['Standing','Walking','Running','Fidget','Dead']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 first=vertices(a.frame_range[0]);last=vertices(a.frame_range[1]);delta=np.linalg.norm(first-last,axis=1)
 report[name]={'loop_max_mm':float(delta.max()*1000),'loop_p99_mm':float(np.percentile(delta,99)*1000),'floor_min_mm':float(min(first[:,2].min(),last[:,2].min())*1000)}
 print('LOOP',name,report[name],flush=True)
 assert delta.max()<.01,(name,float(delta.max()))
 assert min(first[:,2].min(),last[:,2].min())>-.015,(name,report[name])
(p/'work/loop_audit.json').write_text(json.dumps(report,indent=1))
