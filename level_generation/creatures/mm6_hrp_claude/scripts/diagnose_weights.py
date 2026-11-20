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
for role in ['Standing','Attack']:
 rig.animation_data.action=bpy.data.actions[role]
 for frame in range(1,round(bpy.data.actions[role].frame_range[1])+1,2):
  sc.frame_set(frame);obj=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh();c=np.array([v.co[:] for v in mesh.vertices]);obj.to_mesh_clear();length=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1);stretch=length/np.maximum(EL,1e-8)
  for ei in np.argsort(stretch)[-3:][::-1]:
   a,b=map(int,E[ei]);worst.append({'role':role,'time':(frame-1)/32,'ratio':float(stretch[ei]),'rest_length':float(EL[ei]),'delta':float(length[ei]-EL[ei]),'ids':[a,b],'rest':[C[a].tolist(),C[b].tolist()],'weights':[{groups[g.group]:round(g.weight,4) for g in body.data.vertices[i].groups} for i in [a,b]]})
(P/'work/stretch_diagnostic.json').write_text(json.dumps(sorted(worst,key=lambda x:x['delta'],reverse=True)[:15],indent=2));print(json.dumps(sorted(worst,key=lambda x:x['delta'],reverse=True)[:2]))
