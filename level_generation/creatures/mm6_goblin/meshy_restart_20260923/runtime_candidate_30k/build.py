import bpy,json,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');out=ROOT/'runtime_candidate_30k'
s=bpy.data.scenes.new('MM6 Goblin Runtime Geometry Trial 30K');bpy.context.window.scene=s
bpy.ops.import_scene.gltf(filepath=str(ROOT/'repaired_master/mm6_goblin_repaired_master.glb'))
meshes=[o for o in s.objects if o.type=='MESH']
def build():
 try:
  report=[]
  for o in meshes:
   bpy.context.view_layer.objects.active=o;o.select_set(True)
   before=sum(len(p.vertices)-2 for p in o.data.polygons)
   if before>200000:
    mod=o.modifiers.new('Runtime geometry trial','DECIMATE');mod.ratio=28732/before;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
   report.append({'object':o.name,'triangles_before':before,'triangles_after':sum(len(p.vertices)-2 for p in o.data.polygons)})
  for o in s.objects:o.select_set(o.type=='MESH')
  bpy.ops.export_scene.gltf(filepath=str(out/'mm6_goblin_runtime_trial_30k.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False)
  (out/'reduction_report.json').write_text(json.dumps({'method':'Blender collapse decimation, preserved separate plates and rivets','meshes':report,'triangles':sum(r['triangles_after'] for r in report),'rig_and_deformation':'not yet tested','uvs':'not yet created'},indent=2))
  (out/'build_done.txt').write_text('complete')
 except Exception:(out/'error.txt').write_text(traceback.format_exc())
 return None
bpy.app.timers.register(build,first_interval=.1)
print('Reduction scheduled')
