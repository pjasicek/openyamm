import bpy,json,hashlib,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/skirt_rebuild_01');s=bpy.data.scenes['Goblin - Rebuilt Skirt and Belt v2'];bpy.context.window.scene=s
low=next(o for o in s.objects if o.name.startswith('Goblin_SkirtBelt_Low'));mat=low.data.materials[0];bs=mat.node_tree.nodes.get('Principled BSDF');normal=next(n for n in mat.node_tree.nodes if n.type=='NORMAL_MAP');img=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
visible=[s.objects['Goblin_Body_WithFittedWaist'],s.objects['Goblin_PreservedPouch'],low]+[o for o in s.objects if o.type=='MESH' and ('Upper-back plate' in o.name or 'Back plate rivet' in o.name)]
jobs=['front','quarter','back','full','save','verify']
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:(ROOT/'export_checked.txt').write_text('complete');return None
  job=jobs.pop(0);(ROOT/'progress.txt').write_text(job)
  if job in ['front','quarter','back','full']:
   for link in list(bs.inputs['Normal'].links):mat.node_tree.links.remove(link)
   if job=='full':mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
   cam=s.camera;cam.location={'front':(0,-4,0),'quarter':(-3,-4,.5),'back':(0,4,0),'full':(0,-4,0)}[job];cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.15 if job=='full' else .82;s.render.filepath=str(ROOT/('full_baked.png' if job=='full' else job+'_unbaked.png'));bpy.ops.render.render(write_still=True)
  elif job=='save':
   bpy.ops.object.select_all(action='DESELECT');low.select_set(True);bpy.context.view_layer.objects.active=low
   bpy.ops.export_scene.gltf(filepath=str(ROOT/'skirt_belt_1392.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False)
   for o in visible:o.hide_render=False;o.hide_viewport=False;o.hide_set(False);o.select_set(True)
   bpy.ops.export_scene.gltf(filepath=str(ROOT/'goblin_skirt_rebuild_review.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False)
   for o in visible:o.select_set(o==low)
   img.pack();bpy.data.libraries.write(str(ROOT/'skirt_rebuild.blend'),{s},fake_user=True,compress=True)
   for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
     sp=area.spaces.active;sp.shading.type='MATERIAL';sp.region_3d.view_location=(0,0,0);sp.region_3d.view_distance=2.0;sp.region_3d.view_rotation=Vector((0,-4,0)).to_track_quat('Z','Y');sp.region_3d.view_perspective='ORTHO'
  else:
   v=bpy.data.scenes.new('Goblin skirt export verification');bpy.context.window.scene=v;bpy.ops.import_scene.gltf(filepath=str(ROOT/'goblin_skirt_rebuild_review.glb'))
   report={'meshes':[],'triangles':0}
   for o in v.objects:
    if o.type=='MESH':
     count=sum(len(p.vertices)-2 for p in o.data.polygons);report['triangles']+=count;report['meshes'].append({'name':o.name,'triangles':count,'uv_layers':len(o.data.uv_layers),'materials':[m.name for m in o.data.materials]})
   report['sha256']=hashlib.sha256((ROOT/'goblin_skirt_rebuild_review.glb').read_bytes()).hexdigest();(ROOT/'export_verification.json').write_text(json.dumps(report,indent=2)+'\n')
   v.render.engine='CYCLES';v.cycles.samples=24;v.cycles.use_denoising=True;v.cycles.device='CPU';v.world=s.world;v.view_settings.view_transform='AgX';v.render.resolution_x=900;v.render.resolution_y=900;v.render.resolution_percentage=100;v.render.image_settings.file_format='PNG'
   for o in s.objects:
    if o.type in ['LIGHT','CAMERA']:
     cp=o.copy();cp.data=o.data.copy();v.collection.objects.link(cp)
     if o.type=='CAMERA':v.camera=cp
   v.camera.location=(0,-4,0);v.camera.rotation_euler=(-v.camera.location).to_track_quat('-Z','Y').to_euler();v.camera.data.ortho_scale=.82;v.render.filepath=str(ROOT/'export_front.png');bpy.ops.render.render(write_still=True);bpy.context.window.scene=s
  return .1
 except Exception:(ROOT/'export_error.txt').write_text(traceback.format_exc());bpy.context.window.scene=s;return None
bpy.app.timers.register(step,first_interval=.1)
print('Final views and export verification queued.')
