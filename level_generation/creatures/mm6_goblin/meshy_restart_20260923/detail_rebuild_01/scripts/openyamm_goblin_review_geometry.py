import bpy,traceback
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/detail_rebuild_01');s=bpy.data.scenes['Goblin - Complete Low Mesh Detail Test'];bpy.context.window.scene=s
clay=bpy.data.materials.new('Review identical neutral clay');clay.use_nodes=True;bs=clay.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.34,.36,1);bs.inputs['Roughness'].default_value=.7
low=[s.objects['Goblin_Low_Body'],s.objects['Goblin_Low_Pouch'],s.objects['Goblin_Low_SkirtBelt']]+[o for o in s.objects if o.name.startswith('Goblin_Low_BackPlate')]
high=[o for o in s.objects if o.name.startswith('Goblin_DetailBake_')];jobs=['low_front','low_face','low_shins','high_front','high_face']
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:
   s.view_layers[0].material_override=None
   for o in high:o.hide_render=True
   for o in low:o.hide_render=False
   (OUT/'geometry_review_done.txt').write_text('complete');return None
  job=jobs.pop(0);s.view_layers[0].material_override=clay
  for o in high:o.hide_render=not job.startswith('high')
  for o in low:o.hide_render=job.startswith('high')
  z=.79 if job.endswith('face') else -.66 if job.endswith('shins') else 0
  s.camera.location=(0,-4,z);s.camera.rotation_euler=(Vector((0,0,z))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=.47 if z==.79 else .72 if z else 2.15;s.render.filepath=str(OUT/(job+'.png'));bpy.ops.render.render(write_still=True);return .1
 except Exception:(OUT/'geometry_review_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print('Matched source and geometry-only review renders scheduled.')
