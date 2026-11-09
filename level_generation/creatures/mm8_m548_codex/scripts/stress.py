import bpy,sys,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
sys.path.insert(0,str(P/'scripts'));import motion as M
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.68,.56,.62);sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False
sc.render.resolution_x=600;sc.render.resolution_y=600;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.65
out=P/'review/stress';out.mkdir(exist_ok=True)
results=[]
for name,t in [('Standing',0),('Walking',.125),('Walking',.375),('Attack',.45),('Hit',.3),('Death',.7),('Dead',1)]:
 M.pose(name,t);a=M.co();assert a[:,2].min()>-.004
 results.append({'clip':name,'seconds':t,'min_z':float(a[:,2].min()),'max_z':float(a[:,2].max())})
 for view,d in [('side',(1,0,.08)),('quarter',(1,-1,.25))]:
  c=Vector((0,-.06,.36));cam.location=c+Vector(d)*3;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
  sc.render.filepath=str(out/f'{name}_{t}_{view}.png');bpy.ops.render.render(write_still=True)
(out/'checks.json').write_text(json.dumps(results,indent=2));print('STRESS_OK',flush=True)
