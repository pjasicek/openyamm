"""Render the actual exported GLB, every clip in front/profile/three-quarter views."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_min1_a.glb'));sc=bpy.context.scene;r=next(o for o in bpy.data.objects if o.type=='ARMATURE');meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.find_armature()==r];acts={a.name:a for a in bpy.data.actions};rate=sc.render.fps/sc.render.fps_base
for m in bpy.data.materials:
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');base=bs.inputs['Base Color'].links[0].from_node;m.node_tree.nodes.active=base
common.workbench_clay(sc,textured=True);sc.view_settings.view_transform='Standard';sc.display.shading.studiolight_rotate_z=math.radians(35);sc.render.resolution_percentage=100
D=P/'review/frames';D.mkdir(exist_ok=True);report={}
def pose(role,t):
 a=acts[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];f=t*rate;sc.frame_set(int(f),subframe=f%1)
def bounds():
 dg=bpy.context.evaluated_depsgraph_get();vs=[]
 for o in meshes:
  e=o.evaluated_get(dg);m=e.to_mesh();vs.extend([tuple(o.matrix_world@v.co) for v in m.vertices]);e.to_mesh_clear()
 return np.array(vs)
M=json.loads((P/'review/runtime_metrics.json').read_text())
for role,meta in M['clips'].items():
 dur=meta['duration'];ts=list(np.linspace(0,dur,5))
 if role=='Attack':ts[2]=json.loads((P/'review/final_blade_gate.json').read_text())['Attack']['impact_seconds']
 if role=='Cast':ts[2]=json.loads((P/'review/final_blade_gate.json').read_text())['Cast']['impact_seconds']
 ts.sort();cloud=[]
 for t in np.linspace(0,dur,25):pose(role,float(t));cloud.append(bounds())
 cloud=np.concatenate(cloud);lo=cloud.min(0);hi=cloud.max(0);center=(lo+hi)/2;size=max(float(hi[2]-lo[2]),float(np.linalg.norm((hi-lo)[:2])))*1.12;size=max(size,2.5)
 for i,t in enumerate(ts):
  pose(role,float(t));common.render_views(str(D/f'{role}_{i}'),float(center[2]),size,views=['front','left','three_quarter'],resolution=(480,480),target=tuple(center[:2]))
 report[role]={'times_seconds':ts,'frame_bounds_min':lo.tolist(),'frame_bounds_max':hi.tolist(),'ortho_scale':size,'views':['front','left','three_quarter']}
(P/'review/sheet_manifest.json').write_text(json.dumps(report,indent=2))
print('RENDERED all nine exported clips')
