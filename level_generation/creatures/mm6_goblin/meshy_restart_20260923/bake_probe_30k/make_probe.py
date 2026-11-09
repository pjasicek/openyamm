import bpy,json,traceback,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/bake_probe_30k');ROOT.mkdir(exist_ok=True)
previous=bpy.context.scene
assert 'Goblin 30K normal bake proof' not in bpy.data.scenes
s=bpy.data.scenes.new('Goblin 30K normal bake proof');bpy.context.window.scene=s
bpy.ops.import_scene.gltf(filepath=str(ROOT.parent/'runtime_candidate_30k/mm6_goblin_runtime_trial_30k.glb'))
low=max((o for o in s.objects if o.type=='MESH'),key=lambda o:len(o.data.polygons));low.name='Goblin30K_BakeProof'
for o in s.objects:
 if o.type=='MESH' and len(o.data.polygons)==100:o.hide_render=True;o.hide_set(True)
bpy.ops.object.select_all(action='DESELECT');low.select_set(True);bpy.context.view_layer.objects.active=low
if not low.data.uv_layers:low.data.uv_layers.new(name='BakeProofUV')
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008);bpy.ops.object.mode_set(mode='OBJECT')
source=bpy.data.scenes['MM6 Goblin - Quad Remesher Trial 01'].objects['Goblin_QR_Source_DensityGuided']
high=source.copy();high.data=source.data;high.name='DenseMaster_BakeSource';s.collection.objects.link(high);high.hide_viewport=False;high.hide_render=False;high.hide_set(False)
mat=bpy.data.materials.new('Goblin bake proof clay');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.34,.36,1);bs.inputs['Roughness'].default_value=.7
low.data.materials.clear();low.data.materials.append(mat)
img=bpy.data.images.new('Goblin30K_DenseNormal_Proof',width=2048,height=2048,alpha=False);img.colorspace_settings.name='Non-Color';img.filepath_raw=str(ROOT/'normal.png');img.file_format='PNG'
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;mat.node_tree.nodes.active=node
normal=mat.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=1;mat.node_tree.links.new(node.outputs['Color'],normal.inputs['Color'])
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.use_denoising=True
s.render.bake.use_selected_to_active=True;s.render.bake.use_cage=False;s.render.bake.cage_extrusion=.015;s.render.bake.max_ray_distance=.04;s.render.bake.margin=12;s.render.bake.normal_space='TANGENT'
for o in s.objects:o.select_set(False)
low.select_set(True);high.select_set(True);bpy.context.view_layer.objects.active=low
cd=bpy.data.cameras.new('Goblin bake proof camera');cam=bpy.data.objects.new('Goblin bake proof camera',cd);s.collection.objects.link(cam);s.camera=cam;cd.type='ORTHO';cd.ortho_scale=2.15;cam.location=(0,-4,0);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=720;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
s.world=bpy.data.worlds.new('Goblin proof world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.15,.17,.20,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
for name,offset,power,size in [('Key',(-3,-4,5),650,3),('Fill',(4,-2,2),400,4),('Rim',(1,3,4),800,3)]:
 ld=bpy.data.lights.new('Goblin proof '+name,'AREA');ld.energy=power;ld.size=size;ob=bpy.data.objects.new('Goblin proof '+name,ld);s.collection.objects.link(ob);ob.location=offset;ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
report={'low_body_triangles':len(low.data.polygons),'dense_source_triangles':len(high.data.polygons),'normal_resolution':2048,'temporary_uvs':'Smart projection for feasibility proof, not final UV acceptance','cage_extrusion':.015,'max_ray_distance':.04,'scope':'Body normal bake only; no color textures, no topology edits, no rig. Separate rivets hidden; plates retained.'}
(ROOT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
jobs=['bake','unbaked','baked','save']
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:
   bpy.context.window.scene=previous;(ROOT/'done.txt').write_text('complete');return None
  job=jobs.pop(0);(ROOT/'progress.txt').write_text(job)
  if job=='bake':
   bpy.ops.object.bake(type='NORMAL');img.save();high.hide_render=True;high.hide_set(True);high.select_set(False)
  elif job=='save':
   img.pack();bpy.data.libraries.write(str(ROOT/'bake_proof.blend'),{s},fake_user=True,compress=True)
  else:
   if job=='baked':mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
   s.render.filepath=str(ROOT/(job+'.png'));bpy.ops.render.render(write_still=True)
  return .1
 except Exception:
  bpy.context.window.scene=previous;(ROOT/'error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1)
print(json.dumps(report))
