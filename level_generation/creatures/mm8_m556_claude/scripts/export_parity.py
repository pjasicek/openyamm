"""Reimport the delivered portable GLB: dense floor/loop checks, every clip, and flight scale renders."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];names=['Fly','FlyFast','Attack','Hit','Fidget','Death','Dead'];saved={};report={}
def coords(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();a=np.array([obj.matrix_world@v.co for v in m.vertices]);e.to_mesh_clear();return a
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m556.blend'));sc=bpy.context.scene;sc.render.fps=48;rig=bpy.data.objects['Wasp_Rig'];body=bpy.data.objects['Wasp']
for name in names:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];lo,hi=a.frame_range;saved[name]=[];minimum=1e9;first=None;heights=[]
 for f in np.linspace(lo,hi,round((hi-lo)*4)+1):
  sc.frame_set(int(f),subframe=f-int(f));c=coords(body);minimum=min(minimum,float(c[:,2].min()));first=c if first is None else first;last=c;heights.append(float(np.ptp(c[:,2])))
 assert minimum>-.002,(name,minimum)
 loop=float(np.linalg.norm(last-first,axis=1).max())
 if name in ['Fly','FlyFast','Dead']:assert loop<.002,(name,loop)
 report[name]=dict(min_z_dense_192hz=minimum,loop_delta=loop,duration=float((hi-lo)/48),mean_height_m=float(np.mean(heights)),final_bounds=[last.min(0).tolist(),last.max(0).tolist()])
 for frac in np.linspace(0,1,9):
  f=lo+(hi-lo)*frac;sc.frame_set(int(f),subframe=f-int(f));saved[name].append((frac,coords(body)))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=48;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_m556_portable.glb'));sc=bpy.context.scene;sc.render.fps=48;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['Wasp'];assert len(bpy.data.actions)==7
for o in list(bpy.data.objects):
 if o.type=='MESH' and o!=body:bpy.data.objects.remove(o,do_unlink=True)
for name in names:
 a=next(a for a in bpy.data.actions if a.name==name or a.name.endswith('|'+name));rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];lo,hi=a.frame_range;errors=[]
 assert abs((hi-lo)/48-report[name]['duration'])<1e-6
 for frac,ref in saved[name]:
  f=lo+(hi-lo)*frac;sc.frame_set(int(f),subframe=f-int(f));cur=coords(body);tree=KDTree(len(cur))
  for i,c in enumerate(cur):tree.insert(c,i)
  tree.balance();errors.append(max(tree.find(c)[2] for c in ref))
 assert max(errors)<.0002,(name,errors)
 report[name]['max_export_surface_error_m']=max(errors)
(P/'review/export_parity.json').write_text(json.dumps(report,indent=2));print('PARITY',json.dumps(report))
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=sc.render.resolution_y=768;sc.render.resolution_percentage=100;sc.render.film_transparent=True
cam=bpy.data.objects.new('ScaleCamera',bpy.data.cameras.new('ScaleCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.5
cam.location=(0,-4,.5);cam.rotation_euler=(Vector((0,0,.5))-cam.location).to_track_quat('-Z','Y').to_euler()
a=next(a for a in bpy.data.actions if a.name=='Fly' or a.name.endswith('|Fly'));rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for i in range(5):
 sc.frame_set(i*6);sc.render.filepath=str(P/'review'/f'scale_front_{i}.png');bpy.ops.render.render(write_still=True)
