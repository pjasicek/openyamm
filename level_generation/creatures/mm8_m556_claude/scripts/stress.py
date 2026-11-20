"""Inspect actual deformed geometry in isolated static range-of-motion views."""
from pathlib import Path
import sys,bpy,json
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from wasp_pose import base_pose,rotate_world,reset,arms
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/(sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'rig_equipped_v1.blend')))
rig=bpy.data.objects['Wasp_Rig'];m=bpy.data.objects['Wasp'];sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True;sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.55,.62,.64)
sc.render.resolution_x=sc.render.resolution_y=900;sc.render.film_transparent=True
cam=bpy.data.objects.new('StressCamera',bpy.data.cameras.new('StressCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.3
report={}
for pose in ['rest','guard','downstroke','strike','curl']:
 reset(rig)
 if pose!='rest':base_pose(rig,.15625 if pose=='downstroke' else 0)
 if pose=='strike':
  rotate_world(rig,'Thorax','X',13);arms(rig,(.15,-.18,.66),(-.1,-.18,.65),(-.25,-.96,-.13))
 if pose=='curl':
  rotate_world(rig,'Head','Z',30)
  for i in range(1,5):rotate_world(rig,'Abdomen'+str(i),'X',-20)
  for side in ['L','R']:rotate_world(rig,'HindFemur_'+side,'X',45)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=m.evaluated_get(dg)
 report[pose]={'min_z':min(v.co.z for v in ev.data.vertices),'max_z':max(v.co.z for v in ev.data.vertices)}
 for view,location in [('front',(0,-4,.48)),('side',(4,0,.48)),('quarter',(2,-3,1.3))]:
  target=Vector((0,.0,.48));cam.location=location;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/'review'/f'reduced_{pose}_{view}.png');bpy.ops.render.render(write_still=True)
(P/'review/stress_metrics.json').write_text(json.dumps(report,indent=2))
