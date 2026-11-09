"""Reimport the portable GLB and compare actual skin deformation against its editable master."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,kdtree,Vector
P=Path(__file__).resolve().parents[1];manifest={'clips':{n:{'duration':d} for n,d in json.loads((P/'export/export_info.json').read_text())['clips'].items()}};names=['Peasant'];reference={};bind={}
def action(rig,name):
 rig.animation_data_create();rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
 candidates=[a for a in bpy.data.actions if a.name==name or a.name.endswith('|'+name)];assert len(candidates)==1,(name,[a.name for a in bpy.data.actions]);a=candidates[0];rig.animation_data_create();rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];return a
def coords(name):
 o=bpy.data.objects[name];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([o.matrix_world@v.co for v in mesh.vertices]);ev.to_mesh_clear();return co
def rest(rig):
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_pman_v2.blend'));rig=bpy.data.objects['Rig'];rest(rig)
for name in names:bind[name]=coords(name)
for name,info in manifest['clips'].items():
 action(rig,name);reference[name]={}
 for t in sorted(set([i/120 for i in range(math.ceil(info['duration']*120))]+[info['duration']])):
  f=t*30;bpy.context.scene.frame_set(math.floor(f),subframe=f%1);reference[name][t]={n:coords(n) for n in names}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_pman_v2_lod0.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rest(rig);mapping={}
for name in names:
 tree=kdtree.KDTree(len(bind[name]))
 for i,p in enumerate(bind[name]):tree.insert(Vector(p),i)
 tree.balance();dst=coords(name);hits=[tree.find(Vector(p)) for p in dst];assert max(x[2] for x in hits)<.00001;mapping[name]=np.array([x[1] for x in hits])
report={}
for name,samples in reference.items():
 a=action(rig,name);maximum=0
 for t,expected in samples.items():
  f=t*bpy.context.scene.render.fps/bpy.context.scene.render.fps_base;bpy.context.scene.frame_set(math.floor(f),subframe=f%1)
  for n in names:maximum=max(maximum,float(np.linalg.norm(coords(n)-expected[n][mapping[n]],axis=1).max()))
 report[name]={'samples':len(samples),'maximum_vertex_error_m':maximum};assert maximum<.002,(name,maximum)
 if name in ['Standing','Walking','Run','Fidget']:
  delta=np.linalg.norm(samples[max(samples)]['Peasant']-samples[0.0]['Peasant'],axis=1);report[name]['loop_endpoint_max_m']=float(delta.max());report[name]['loop_endpoint_p99_m']=float(np.percentile(delta,99));assert delta.max()<.02,(name,'loop endpoint',float(delta.max()))
print('EXPORT_PARITY',report);(P/'work/export_parity.json').write_text(json.dumps(report,indent=2))
