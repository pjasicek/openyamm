"""Reimport the actual portable GLB; validate clips, rigid swords, skin weights and standing scale."""
import bpy,json,hashlib,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];source=P/'export/mm8_m624_runtime_lod0.glb';bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=bpy.data.objects['Body'];clips={}
for a in bpy.data.actions:
 name=a.name.split('|')[-1];clips[name]=(a.frame_range[1]-a.frame_range[0])/bpy.context.scene.render.fps
assert len(clips)==9,(clips,bpy.context.scene.render.fps)
for ob in bpy.data.objects:
 if ob.name=='Body' or ob.name.endswith('_Weapon'):
  for v in ob.data.vertices:assert 0<sum(g.weight>1e-5 for g in v.groups)<=4 and abs(sum(g.weight for g in v.groups)-1)<.0001,(ob.name,v.index,[(ob.vertex_groups[g.group].name,g.weight)for g in v.groups])
for sd in ['L1','L2','L3','R1','R2','R3']:
 ob=bpy.data.objects[sd+'_Weapon'];assert all(all(ob.vertex_groups[g.group].name==sd+'_Sword' for g in v.groups if g.weight>1e-5)for v in ob.data.vertices)
rig.animation_data.action=next(a for a in bpy.data.actions if a.name.split('|')[-1]=='Standing');bpy.context.scene.frame_set(int(rig.animation_data.action.frame_range[0]));bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();coords=np.array([(o.evaluated_get(deps).matrix_world@v.co)[:]for o in bpy.data.objects if (o.name=='Body' or o.name.endswith('_Weapon'))for v in o.evaluated_get(deps).data.vertices]);height=float(np.ptp(coords[:,2]));assert 2<height<4,height
report={'glb_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'clips':clips,'bones':len(rig.data.bones),'standing_assembly_height_m':height,'standing_bbox_blender':[coords.min(0).tolist(),coords.max(0).tolist()],'rigid_weapons':6,'max_influences':4};(P/'work/export_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
# Render the actual exported posed surface under neutral light.
from mathutils import Vector
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.render.resolution_x=sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('World');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.35,.4,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.6
for n,loc,energy,size in [('Key',(3,-4,6),800,4),('Fill',(-4,-2,3),500,4),('Rim',(1,4,5),750,3)]:
 light=bpy.data.objects.new(n,bpy.data.lights.new(n,'AREA'));sc.collection.objects.link(light);light.location=loc;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler();light.data.energy=energy;light.data.shape='DISK';light.data.size=size
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for view,loc,target,scale in [('front',(0,-6,2),(0,0,1.4),4.1),('quarter',(4,-6,3),(0,0,1.4),4.1),('back',(0,6,2),(0,0,1.4),4.1),('face',(0,-4,2.05),(-.025,-.03,2.0),.58)]:
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(P/f'review/export_{view}.png');bpy.ops.render.render(write_still=True)
