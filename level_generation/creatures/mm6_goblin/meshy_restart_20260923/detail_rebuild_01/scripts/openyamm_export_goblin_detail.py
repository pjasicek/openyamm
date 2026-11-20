import bpy,json,hashlib,traceback
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/detail_rebuild_01');work=bpy.data.scenes['Goblin - Complete Low Mesh Detail Test']
s=bpy.data.scenes.new('Goblin - Simplified 10577 Review');bpy.context.window.scene=s
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.device='CPU';s.cycles.use_denoising=True;s.world=work.world;s.view_settings.view_transform='AgX';s.render.resolution_x=900;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
meshes=[]
for o in work.objects:
 if o.type in ['CAMERA','LIGHT'] or o.name in ['Goblin_Low_Body','Goblin_Low_Pouch','Goblin_Low_SkirtBelt','Goblin_Low_BackPlate_L','Goblin_Low_BackPlate_R']:
  cp=o.copy();cp.data=o.data.copy();s.collection.objects.link(cp);cp.hide_render=False;cp.hide_viewport=False;cp.hide_set(False)
  if cp.type=='MESH':meshes.append(cp)
  if cp.type=='CAMERA':s.camera=cp
s.camera.location=(0,-4,0);s.camera.rotation_euler=(-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=2.15
report={'stage':'static review candidate, not accepted for rigging or runtime','meshes':[],'normal_maps':[],'limitations':['No color/roughness textures or rig yet.','Local normal projection defects remain around the left shin rim, jewelry and thin armor edges.','Head/mouth reduced while retaining opening, jaw and visible teeth; no facial animation topology.','Weighted decimation is a static geometry test; joint deformation remains untested.','Minor fused armor relief is approximated by reduced geometry plus normal map, not all manually rebuilt.','Source left-ear jewelry cleanup is outstanding.','Sword not included.']}
def run():
 try:
  bpy.context.window.scene=s;bpy.ops.object.select_all(action='DESELECT')
  imgs=set()
  for o in meshes:
   o.select_set(True);report['meshes'].append({'name':o.name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'uv_layers':len(o.data.uv_layers)})
   for m in o.data.materials:
    if m and m.use_nodes:
     for n in m.node_tree.nodes:
      if n.type=='TEX_IMAGE' and n.image:imgs.add(n.image)
  for img in imgs:
   img.pack();report['normal_maps'].append({'name':img.name,'width':img.size[0],'height':img.size[1]})
  report['triangles']=sum(o['triangles'] for o in report['meshes']);assert report['triangles']==10577,report['triangles']
  bpy.context.view_layer.objects.active=meshes[0]
  path=OUT/'goblin_simplified_10577.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_tangents=True)
  report['glb_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();(OUT/'final_report.json').write_text(json.dumps(report,indent=2)+'\n')
  for area in bpy.context.screen.areas:
   if area.type=='VIEW_3D':
    sp=area.spaces.active;sp.shading.type='MATERIAL';sp.region_3d.view_location=(0,0,0);sp.region_3d.view_distance=2.5;sp.region_3d.view_rotation=Vector((0,-4,0)).to_track_quat('Z','Y');sp.region_3d.view_perspective='ORTHO'
  bpy.data.libraries.write(str(OUT/'goblin_simplified_10577.blend'),{s},fake_user=True,compress=True)
  v=bpy.data.scenes.new('Goblin 10577 Export Verification');bpy.context.window.scene=v;bpy.ops.import_scene.gltf(filepath=str(path))
  stats={'triangles':0,'meshes':[]}
  for o in v.objects:
   if o.type=='MESH':
    n=sum(len(p.vertices)-2 for p in o.data.polygons);stats['triangles']+=n;stats['meshes'].append({'name':o.name,'triangles':n,'uv_layers':len(o.data.uv_layers)})
  assert stats['triangles']==10577;stats['sha256']=report['glb_sha256'];(OUT/'export_verification.json').write_text(json.dumps(stats,indent=2)+'\n')
  for o in s.objects:
   if o.type in ['CAMERA','LIGHT']:
    cp=o.copy();cp.data=o.data.copy();v.collection.objects.link(cp)
    if cp.type=='CAMERA':v.camera=cp
  v.world=s.world;v.render.engine='CYCLES';v.cycles.samples=24;v.cycles.device='CPU';v.cycles.use_denoising=True;v.view_settings.view_transform='AgX';v.render.resolution_x=900;v.render.resolution_y=1000;v.render.resolution_percentage=100;v.render.image_settings.file_format='PNG';v.render.filepath=str(OUT/'export_front.png');bpy.ops.render.render(write_still=True)
  bpy.context.window.scene=s;(OUT/'export_done.txt').write_text('complete')
 except Exception:(OUT/'export_error.txt').write_text(traceback.format_exc());bpy.context.window.scene=s
 return None
bpy.app.timers.register(run,first_interval=.1);print('Clean review scene, packed GLB and reimport verification scheduled.')
