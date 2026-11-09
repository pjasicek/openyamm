"""Reimport the delivered LOD0 and compare every frame/half-frame with the authored surface."""
import bpy,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene
rest=np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices])
source_weights=[{o.vertex_groups[g.group].name:float(g.weight) for g in v.groups if g.weight>1e-6} for v in o.data.vertices]
labels={name:np.array([v.value for v in o.data.attributes[name].data]) for name in ('piece','finger') if name in o.data.attributes}
def select(a):
 r.animation_data.action=a
 if a:r.animation_data.action_slot=a.slots[0]
def surface():
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
 V=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',V);V=V.reshape(-1,3)
 M=np.array(o.matrix_world);V=V@M[:3,:3].T+M[:3,3];ev.to_mesh_clear();return V
reference={};stride={}
for name in ('Standing','Walking','Hit','Death','Fidget'):
 a=bpy.data.actions[name];select(a);times=np.arange(0,a.frame_range[1]+.01,.5);values=[]
 for f in times:
  sc.frame_set(int(f),subframe=float(f%1));values.append(surface())
 reference[name]=(times,np.array(values))
 if name=='Standing':
  floor=float(values[0][:,2].min());height=float(values[0][:,2].max()-floor)
  stride.update(standing_height_m=height,standing_floor_m=floor,native_height_game_units=175.7,recommended_scale=175.7/height)
 if name=='Walking':
  for side,phase in [('L',.75),('R',.25)]:
   xs=[];ys=[]
   for f in times:
    rel=(f/24-phase)%1
    if .12<rel<.40:
     sc.frame_set(int(f),subframe=float(f%1));xs.append(rel*.8);ys.append(float(r.pose.bones[f'B_{side}_Foot'].head.y))
   v=float(np.polyfit(xs,ys,1)[0]);stride[side+'_stride_m']=abs(v)*.8
reference['Dead']=(np.array([0,15,30]),np.repeat(reference['Death'][1][-1:,:,:],3,axis=0))
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(p/'export/mm6_pfem_runtime_lod0.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');r.name='Rig'
o=max((o for o in bpy.data.objects if o.type=='MESH'),key=lambda x:len(x.data.vertices));o.name='Body'
actions={}
for a in bpy.data.actions:
 name=a.name.split('|')[-1]
 for expected in reference:
  if name==expected or name.endswith('_'+expected):actions[expected]=a
print('IMPORTED ACTIONS',list(actions),[a.name for a in bpy.data.actions])
assert set(actions)==set(reference)
select(None)
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
tree=kdtree.KDTree(len(rest))
for i,v in enumerate(rest):tree.insert(Vector(v),i)
tree.balance()
mapping=[];distance=[]
for v in o.data.vertices:
 candidates=tree.find_range(o.matrix_world@v.co,.00001)
 w={o.vertex_groups[g.group].name:float(g.weight) for g in v.groups if g.weight>1e-6}
 def cost(candidate):
  sw=source_weights[candidate[1]]
  return sum(abs(w.get(n,0)-sw.get(n,0)) for n in set(w)|set(sw))
 assert candidates
 _,i,d=min(candidates,key=cost);mapping.append(i);distance.append(d)
mapping=np.array(mapping);assert max(distance)<.00001,max(distance)
for name,values in labels.items():
 at=o.data.attributes.get(name) or o.data.attributes.new(name,'INT','POINT')
 at.data.foreach_set('value',values[mapping].tolist())
report={}
for name,(times,values) in reference.items():
 a=actions[name];select(a);worst=(0,None);floor=(10,None);actual=[]
 for j,f in enumerate(times):
  sc.frame_set(int(f),subframe=float(f%1));V=surface()
  error=float(np.linalg.norm(V-values[j][mapping],axis=1).max())
  if error>worst[0]:
   worst=(error,float(f));bad=int(np.linalg.norm(V-values[j][mapping],axis=1).argmax())
   debug={'export_vertex':bad,'source_vertex':int(mapping[bad]),'piece':int(labels['piece'][mapping[bad]]),'rest':rest[mapping[bad]].tolist(),'export_weights':{o.vertex_groups[g.group].name:float(g.weight) for g in o.data.vertices[bad].groups if g.weight>1e-6},'source_weights':source_weights[mapping[bad]]}
  low=float(V[:,2].min())
  if low<floor[0]:floor=(low,float(f))
  actual.append(V)
 report[name]={'max_surface_error_m':worst,'min_z_m':floor,'samples':len(times),'duration_seconds':float(a.frame_range[1]/30)}
 print('ROUNDTRIP',name,report[name])
 print('ROUNDTRIP WORST',name,debug)
 assert worst[0]<.001,(name,worst)
 assert floor[0]>-.002,(name,floor)
 a.name=name;a.use_fake_user=True
select(actions['Standing']);sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/roundtrip.blend'))
(p/'work/roundtrip_gate.json').write_text(json.dumps(report,indent=2))
stride['stride_length_m']=float(np.mean([stride['L_stride_m'],stride['R_stride_m']]))
(p/'work/runtime_fit.json').write_text(json.dumps(stride,indent=2))
print('RUNTIME FIT',stride)
