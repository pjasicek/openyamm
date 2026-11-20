"""Inspect pilot extremes and locate edge-stretch causes on the evaluated skinned mesh."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
C=np.array([v.co[:] for v in body.data.vertices]);E=np.array([e.vertices[:] for e in body.data.edges]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1);groups={g.index:g.name for g in body.vertex_groups}
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=True;sc.world=bpy.data.worlds.new('World');sc.world.color=(.12,.12,.14);sc.render.resolution_x=1000;sc.render.resolution_y=760;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';worst=[]
for role,t in [('Standing',0),('Standing',.5625),('Running',.25),('Attack',.75),('Attack',1.094),('Attack',1.375),('Cast',1.094),('Hit',.219),('Fidget',.9),('Death',.75),('Death',1.5),('Dead',0)]:
 rig.animation_data.action=bpy.data.actions[role];sc.frame_set(1+round(t*sc.render.fps));obj=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh();c=np.array([v.co[:] for v in mesh.vertices]);obj.to_mesh_clear();stretch=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1)/np.maximum(EL,1e-8)
 for ei in np.argsort(stretch)[-6:][::-1]:
  a,b=map(int,E[ei]);worst.append({'role':role,'time':t,'ratio':float(stretch[ei]),'rest_length':float(EL[ei]),'ids':[a,b],'rest':[C[a].tolist(),C[b].tolist()],'posed':[c[a].tolist(),c[b].tolist()],'weights':[{groups[g.group]:round(g.weight,4) for g in body.data.vertices[i].groups} for i in [a,b]]})
 for view,pos,target,size in [('front',(0,-6,1.1),(0,0,1.1),3.2),('quarter',(4,-6,2.7),(0,0,1.1),3.2),('side',(6,0,1.1),(0,0,1.1),2.8)]:
  cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(P/'review'/f'pilot_{role}_{t}_{view}.png');bpy.ops.render.render(write_still=True)
(P/'work/pilot_stretch_edges.json').write_text(json.dumps(worst,indent=2));print('worst',max(w['ratio'] for w in worst))
# Export an isolated clay GLB for the shared viewer.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig;rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
(P/'export').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P/'export/harpy_pilot.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=False)
