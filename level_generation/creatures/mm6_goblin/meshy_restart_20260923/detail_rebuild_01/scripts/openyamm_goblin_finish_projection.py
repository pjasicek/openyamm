import bpy,json,traceback
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/detail_rebuild_01');s=bpy.data.scenes['Goblin - Complete Low Mesh Detail Test'];bpy.context.window.scene=s
body=s.objects['Goblin_Low_Body'];pouch=s.objects['Goblin_Low_Pouch'];targets=[body,pouch]+[o for o in s.objects if o.name.startswith('Goblin_Low_BackPlate')]
mat=body.data.materials[0];bs=mat.node_tree.nodes.get('Principled BSDF');normal=next(n for n in mat.node_tree.nodes if n.type=='NORMAL_MAP');img=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
for link in list(bs.inputs['Normal'].links):mat.node_tree.links.remove(link)
high=s.objects['Goblin_DetailBake_DenseBody'];hardware=[o for o in s.objects if o.name.startswith('Goblin_DetailBake_') and o!=high]
cages={}
for o in targets:
 c=o.copy();c.data=o.data.copy();c.name='Goblin_FinalBakeCage_'+o.name;s.collection.objects.link(c);c.hide_render=True;c.hide_set(True)
 coords=[v.co.copy() for v in o.data.vertices];normals=[v.normal.copy() for v in o.data.vertices]
 for v,co,n in zip(c.data.vertices,coords,normals):
  z=co.z;amount=(.007 if z>.67 else .035 if -.81<z<-.45 else .019) if o==body else .012
  v.co=co+n*amount
 cages[o.name]=c
s.render.bake.use_cage=True;s.render.bake.max_ray_distance=.075;s.render.bake.use_selected_to_active=True
jobs=[('bake',o.name) for o in targets]+[('render',v) for v in ['front','face','back','quarter']];first=True

def step():
 global first
 try:
  bpy.context.window.scene=s
  if not jobs:(OUT/'final_projection_done.txt').write_text('complete');return None
  job,name=jobs.pop(0);(OUT/'final_projection_progress.txt').write_text(job+' '+name)
  if job=='bake':
   o=s.objects[name];sources=[high] if o in [body,pouch] else hardware;bpy.ops.object.select_all(action='DESELECT')
   for h in sources:h.hide_render=False;h.hide_set(False);h.select_set(True)
   o.select_set(True);bpy.context.view_layer.objects.active=o;s.render.bake.use_clear=first;s.render.bake.cage_object=cages[o.name];bpy.ops.object.bake(type='NORMAL');first=False
   for h in sources:h.select_set(False);h.hide_render=True;h.hide_set(True)
   img.save()
  else:
   mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal']);target=Vector((0,0,.79)) if name=='face' else Vector();s.camera.location={'front':(0,-4,0),'face':(0,-4,.79),'back':(0,4,0),'quarter':(-3,-4,.65)}[name];s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=.47 if name=='face' else 2.15;s.render.filepath=str(OUT/('final_'+name+'.png'));bpy.ops.render.render(write_still=True)
  return .1
 except Exception:(OUT/'final_projection_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print('Final region-sized cage bake scheduled.')
