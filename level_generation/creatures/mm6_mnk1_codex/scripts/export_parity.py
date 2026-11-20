"""Compare every exported deformed point against the editable master at 60 Hz."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm6_mnk1.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
pieces=np.array([v.value for v in b.data.attributes['piece'].data])
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();rest=np.array([tuple(v.co) for v in b.data.vertices]);cache={}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];samples=[]
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();samples.append(np.array([tuple(v.co) for v in m.vertices],np.float32));ev.to_mesh_clear()
 cache[a.name]=samples
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'export/mm6_mnk1.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');b=bpy.data.objects['Monk'];sc=bpy.context.scene
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();co=np.array([tuple(b.matrix_world@v.co) for v in b.data.vertices]);tree=KDTree(len(rest))
for i,q in enumerate(rest):tree.insert(q,i)
tree.balance();found=[tree.find(q) for q in co];dist=np.array([x[2] for x in found]);idx=np.array([x[1] for x in found])
assert dist.max()<1e-5,dist.max()
labels=pieces[idx];skin=np.where(np.isin(labels,[2,3]))[0]
cloth_faces=[list(f.vertices) for f in b.data.polygons if all(labels[i]==0 for i in f.vertices)]
directions=[Vector((math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e))) for e in [0,math.pi/6,-math.pi/6] for a in np.arange(8)*math.pi/4]+[Vector((0,0,1)),Vector((0,0,-1))]
visibility={'hand_vertices_with_uv_duplicates':len(skin),'views':26,'samples':0,'max_visible_hand_vertices':0,'worst_time_s':None}

report={'rest_max_error_m':float(dist.max()),'bones':len(r.data.bones),'clips':{}}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];name=a.name.split('@')[-1].split('|')[-1];mx=0;f0=a.frame_range[0]
 for i,expected in enumerate(cache[name]):
  f=f0+i*sc.render.fps/60;sc.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=np.array([tuple(b.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();mx=max(mx,float(np.linalg.norm(P-expected[idx],axis=1).max()))
  if name=='Standing':
   tree=BVHTree.FromPolygons(P,cloth_faces);count=sum(any(tree.ray_cast(Vector(P[j]),d,3)[0] is None for d in directions) for j in skin)
   visibility['samples']+=1
   if count>visibility['max_visible_hand_vertices']:visibility['max_visible_hand_vertices']=count;visibility['worst_time_s']=i/60
 report['clips'][name]={'samples':len(cache[name]),'max_surface_error_m':mx};print('PARITY',name,mx)
# Blender import reconstructs bone rest frames; allow 0.1 mm for float transform accumulation.
report['tolerance_m']=.0001
report['pass']=all(c['max_surface_error_m']<.0001 for c in report['clips'].values()) and len(report['clips'])==9
(p/'review/export_parity.json').write_text(json.dumps(report,indent=2));assert report['pass'],report

visibility['pass']=visibility['max_visible_hand_vertices']==0 and visibility['samples']==121
(p/'review/review1_runtime_occlusion.json').write_text(json.dumps(visibility,indent=2))
assert visibility['pass'],visibility
