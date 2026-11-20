"""Inspect each actual runtime colour LOD at the repaired hips, in every accepted role."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
D=P/'review/round3';frames=D/'lod_frames';frames.mkdir(exist_ok=True)
poses=[('Standing',0),('Walking',.2),('Running',.15),('Attack',.95),('Cast',1.52),('Hit',.2),('Fidget',1),('Death',1.4),('Dead',0)]
for level in range(4):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(D/f'lod{level}.glb'));sc=bpy.context.scene;r=next(o for o in sc.objects if o.type=='ARMATURE');acts={a.name:a for a in bpy.data.actions};rate=sc.render.fps/sc.render.fps_base
 for m in bpy.data.materials:
  bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');m.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
 common.workbench_clay(sc,textured=True);sc.view_settings.view_transform='Standard';sc.display.shading.studiolight_rotate_z=.6;sc.render.resolution_percentage=100
 for role,t in poses:
  a=acts[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];f=t*rate;sc.frame_set(int(f),subframe=f%1)
  c=r.matrix_world@r.pose.bones['B_Pelvis'].head;c.z-=.13
  common.render_views(str(frames/f'LOD{level}_{role}'),float(c.z),1.08,views=['front','back'],resolution=(480,480),target=tuple(c[:2]))
(D/'lod_frames.json').write_text(json.dumps({'poses':poses,'lods':4,'views':['front','back'],'source':'Final body GLB; forced colour LOD per copy, unchanged animation buffers.'},indent=2))
