import bpy,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/runtime_candidate_30k');out=ROOT/'review'
s=bpy.data.scenes.new('MM6 Goblin Runtime 30K Export Check');bpy.context.window.scene=s
bpy.ops.import_scene.gltf(filepath=str(ROOT/'mm6_goblin_runtime_trial_30k.glb'))
meshes=[o for o in s.objects if o.type=='MESH'];report=[]
lo=Vector((1e9,1e9,1e9));hi=-lo
for o in meshes:
 o.name='Restart Goblin Master '+o.name
 for c in o.bound_box:
  p=o.matrix_world@Vector(c)
  for i in range(3):lo[i]=min(lo[i],p[i]);hi[i]=max(hi[i],p[i])
 report.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'uv_layers':len(o.data.uv_layers),'materials':len(o.data.materials)})
center=(lo+hi)/2;height=hi.z-lo.z
cd=bpy.data.cameras.new('Master review camera');cam=bpy.data.objects.new('Master review camera',cd);s.collection.objects.link(cam);s.camera=cam;cd.type='ORTHO';cd.ortho_scale=height*1.14
s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=800;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False
s.display.shading.light='STUDIO';s.display.shading.studiolight_rotate_z=.25;s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.53,.55,.57);s.display.shading.show_shadows=False;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.display.shading.curvature_ridge_factor=1.2;s.display.shading.curvature_valley_factor=.8;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('Master review neutral');s.world.color=(.065,.07,.08);s.view_settings.view_transform='Standard'
info={'scene':s.name,'mesh_inventory':report,'bounds_min':list(lo),'bounds_max':list(hi),'height_blender_units':height,'rig_count':sum(o.type=='ARMATURE' for o in s.objects),'images':0,'render_note':'Neutral clay geometry review; source has no texture images.'};(ROOT/'inspection.json').write_text(json.dumps(info,indent=2));print(json.dumps(info))
jobs=[('front',(0,-4,0),center,height*1.14),('right',(-4,0,0),center,height*1.14),('back',(0,4,0),center,height*1.14),('left',(4,0,0),center,height*1.14),('quarter',(-3,-4,1),center,height*1.14),('rear_quarter',(3,4,1),center,height*1.14),('above',(0,-2,4),center,height*1.14),('below',(0,-2,-4),center,height*1.14)]
def step():
 try:
  if not jobs:(out/'done.txt').write_text('complete');return None
  name,offset,target,scale=jobs.pop(0);cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale;s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True);return .1
 except Exception:(out/'error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1)
