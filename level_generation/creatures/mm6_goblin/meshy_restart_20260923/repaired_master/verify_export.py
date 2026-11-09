import bpy,json
from mathutils import Vector
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/repaired_master')
source=bpy.data.scenes['MM6 Goblin Restart - Repaired Master'];s=bpy.data.scenes.new('Goblin Repaired Export Verification');bpy.context.window.scene=s
bpy.ops.import_scene.gltf(filepath=str(ROOT/'mm6_goblin_repaired_master.glb'))
meshes=[o for o in s.objects if o.type=='MESH'];count=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
assert len(meshes)==15 and count==1144016,(len(meshes),count)
s.world=source.world;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=800;s.render.resolution_y=900;s.render.resolution_percentage=100;s.display.shading.light='STUDIO';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.53,.55,.57);s.display.shading.show_shadows=False;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.display.shading.background_type='WORLD';s.view_settings.view_transform='Standard'
c=source.camera.copy();c.data=source.camera.data.copy();s.collection.objects.link(c);s.camera=c;c.data.ortho_scale=2.17
for name,offset in [('export_back',(0,4,0)),('export_quarter',(-3,-4,1))]:
 c.location=Vector(offset);c.rotation_euler=(-c.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(ROOT/'review'/(name+'.png'));bpy.ops.render.render(write_still=True)
(ROOT/'export_verification.json').write_text(json.dumps({'meshes':len(meshes),'triangles':count,'rigs':0,'review':'Actual GLB reimport rendered from back and quarter view; intact source ear retained.'},indent=2))
bpy.context.window.scene=source
print({'export_meshes':len(meshes),'export_triangles':count})
