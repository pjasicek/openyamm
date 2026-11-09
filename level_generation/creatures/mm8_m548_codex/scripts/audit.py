"""Check exported surfaces against the editable master, subframes, loops and rigid tips."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];meta=json.loads((P/'work/animation_info.json').read_text());FPS=meta['fps']
def coords(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();points=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();return points
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m548.blend'));rig=bpy.data.objects['CrystalDragonRig'];body=bpy.data.objects['CrystalDragon'];sc=bpy.context.scene;expected={}
for clip,m in meta['clips'].items():
 rig.animation_data.action=bpy.data.actions[clip];expected[clip]=[]
 for t in np.linspace(0,m['duration'],9):
  frame=1+t*FPS;sc.frame_set(math.floor(frame),subframe=frame%1);expected[clip].append((float(t),coords(body)))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m548.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['CrystalDragon'];sc=bpy.context.scene;sc.render.fps=FPS
names={a.name:a for a in bpy.data.actions};report={}
rest=np.array([tuple(v.co) for v in body.data.vertices]);edges=np.array([tuple(e.vertices) for e in body.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
valid=length>.003
for clip,m in meta['clips'].items():
 action=names.get(clip) or next(a for n,a in names.items() if n.endswith('|'+clip));rig.animation_data.action=action
 if action.slots:rig.animation_data.action_slot=action.slots[0]
 error=0
 for t,points in expected[clip]:
  frame=t*FPS;sc.frame_set(math.floor(frame),subframe=frame%1)
  tree=KDTree(len(points))
  for i,point in enumerate(points):tree.insert(point,i)
  tree.balance();error=max(error,max(tree.find(p)[2] for p in coords(body)))
 assert error<.001,(clip,'export surface mismatch',error)
 low=10;stretch=1;maxweight=max(len([g for g in v.groups if g.weight>1e-6]) for v in body.data.vertices)
 for sample in range(round(m['duration']*FPS*2)+1):
  sc.frame_set(sample//2,subframe=sample%2/2);a=np.array([tuple(p) for p in coords(body)])
  low=min(low,float(a[:,2].min()));ratio=np.linalg.norm(a[edges[:,0]]-a[edges[:,1]],axis=1)[valid]/length[valid];stretch=max(stretch,float(np.percentile(ratio,99)))
 assert low>-.01,(clip,'floor',low);assert maxweight<=4
 gap=None
 if m['loop'] or clip=='Dead':
  sc.frame_set(0);a=np.array([tuple(p) for p in coords(body)]);sc.frame_set(round(m['duration']*FPS));b=np.array([tuple(p) for p in coords(body)]);gap=float(np.linalg.norm(a-b,axis=1).max());assert gap<.0001,(clip,'loop',gap)
 report[clip]={'surface_error_m':error,'min_z_m':low,'edge_stretch_p99_max':stretch,'loop_gap_m':gap,'subframe_samples':round(m['duration']*FPS*2)+1}
 print('AUDIT',clip,report[clip],flush=True)
(P/'work/export_audit.json').write_text(json.dumps(report,indent=2))
print('EXPORT_AUDIT_PASS',flush=True)
