"""Check actual runtime surfaces, floor contact, loop closure, weights and roller rigidity."""
import bpy,json,math,struct,hashlib,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];meta=json.loads((P/'work/animation_info.json').read_text());FPS=meta['fps']
names=['Juggernaut','Rubble','Eyes','Flash']
raw=(P/'export/mm8_m608.glb').read_bytes();size=struct.unpack_from('<I',raw,12)[0];document=json.loads(raw[20:20+size]);mesh_names={n['name']:document['meshes'][n['mesh']]['name'] for n in document['nodes'] if 'mesh' in n}
node_names=[n['name'] for n in document['nodes'] if 'name' in n]
assert len(node_names)==len(set(node_names)), 'Duplicate runtime node names'
def mesh(name):
 o=bpy.data.objects[name]
 return o if o.type=='MESH' else next(c for c in bpy.data.objects if c.type=='MESH' and c.data.name==mesh_names[name])
def coords(o):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();p=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear();return p
def visible(name,clip,t):
 death=clip=='Dead' or (clip=='Death' and t>=.25)
 if name=='Rubble':return death
 if name=='Flash':return clip=='Attack' and .95<t<1.09
 return not death
def setaction(rig,action):
 rig.animation_data.action=action
 if action.slots:rig.animation_data.action_slot=action.slots[0]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m608.blend'));rig=bpy.data.objects['JuggernautRig'];sc=bpy.context.scene;expected={}
for clip,m in meta['clips'].items():
 setaction(rig,bpy.data.actions[clip]);expected[clip]=[]
 for t in np.linspace(0,m['duration'],13):
  f=1+t*FPS;sc.frame_set(math.floor(f),subframe=f%1)
  expected[clip].append((float(t),{name:coords(mesh(name)) for name in names if visible(name,clip,t)}))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=FPS;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m608.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;sc.render.fps=FPS
for name in names:
 o=bpy.data.objects[name]
 if o.type=='EMPTY':o.animation_data_clear();o.scale=(1,1,1)
report={};body=mesh('Juggernaut')
for clip,m in meta['clips'].items():
 action=next(a for a in bpy.data.actions if a.name==clip or a.name.endswith('|'+clip));setaction(rig,action);error=0;low=10
 for t,meshes in expected[clip]:
  f=t*FPS;sc.frame_set(math.floor(f),subframe=f%1)
  for name,points in meshes.items():
   tree=KDTree(len(points))
   for i,p in enumerate(points):tree.insert(p,i)
   tree.balance();error=max(error,max(tree.find(p)[2] for p in coords(mesh(name))))
 assert error<.001,(clip,'surface mismatch',error)
 for frame in range(round(m['duration']*FPS*2)+1):
  t=frame/(FPS*2);sc.frame_set(frame//2,subframe=frame%2/2)
  for name in names:
   if visible(name,clip,t):low=min(low,min(v.z for v in coords(mesh(name))))
 assert low>-.004,(clip,'floor',low)
 loop=None
 if m['loop'] or clip=='Dead':
  loop=0
  for name in names:
   if not visible(name,clip,0):continue
   sc.frame_set(0);a=np.array([p[:] for p in coords(mesh(name))]);sc.frame_set(round(m['duration']*FPS));b=np.array([p[:] for p in coords(mesh(name))]);loop=max(loop,float(np.linalg.norm(a-b,axis=1).max()))
  assert loop<.0001,(clip,'loop',loop)
 report[clip]={'surface_error_m':error,'min_z_m':low,'loop_gap_m':loop,'subframe_samples':round(m['duration']*FPS*2)+1}
 print('AUDIT',clip,report[clip],flush=True)
for o in [mesh(n) for n in names]:
 assert max(len([g for g in v.groups if g.weight>1e-6]) for v in o.data.vertices)<=4
 assert all(abs(sum(g.weight for g in v.groups)-1)<1e-4 for v in o.data.vertices)
for r in ['Roller_0','Roller_1','Roller_2']:
 group=body.vertex_groups[r].index;owned=[v for v in body.data.vertices if any(g.group==group and g.weight>.99 for g in v.groups)];assert len(owned)>20
 assert all(len([g for g in v.groups if g.weight>1e-6])==1 for v in owned)
(P/'work/export_audit.json').write_text(json.dumps({'clips':report,'bones':len(rig.data.bones),'maximum_influences':4,'rigid_rollers':3,'export_sha256':hashlib.sha256(raw).hexdigest()},indent=2));print('EXPORT_AUDIT_PASS',flush=True)
