import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');OUT=ROOT/'detail_rebuild_01'
s=bpy.data.scenes['Goblin - Complete Low Mesh Detail Test'];bpy.context.window.scene=s
body=s.objects['Goblin_Low_Body'];pouch=s.objects['Goblin_Low_Pouch'];plates=[o for o in s.objects if o.name.startswith('Goblin_Low_BackPlate')];targets=[body,pouch]+plates
bpy.ops.object.select_all(action='DESELECT')
for o in targets:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.006);bpy.ops.object.mode_set(mode='OBJECT')
mat=bpy.data.materials.new('Goblin Low Body Pouch Plates Normal');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.34,.36,1);bs.inputs['Roughness'].default_value=.7
img=bpy.data.images.new('Goblin_Low_DetailNormal_2048',width=2048,height=2048,alpha=False);img.generated_color=(.5,.5,1,1);img.colorspace_settings.name='Non-Color';img.filepath_raw=str(OUT/'body_pouch_plates_normal.png');img.file_format='PNG'
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;mat.node_tree.nodes.active=tex
normal=mat.node_tree.nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color'])
for o in targets:o.data.materials.clear();o.data.materials.append(mat)
def copy(o,name):
 cp=o.copy();cp.data=o.data;cp.name=name;s.collection.objects.link(cp);cp.hide_viewport=False;cp.hide_render=True;cp.hide_set(True);return cp
src=bpy.data.scenes['MM6 Goblin - Quad Remesher Trial 01'].objects['Goblin_QR_Source_DensityGuided'];high=copy(src,'Goblin_DetailBake_DenseBody')
old=bpy.data.scenes['Goblin - Rebuilt Skirt and Belt v2'];hardware=[copy(o,'Goblin_DetailBake_'+o.name) for o in old.objects if o.type=='MESH' and ('Back plate rivet' in o.name or 'Upper-back plate' in o.name)]
s.render.bake.use_selected_to_active=True;s.render.bake.use_cage=False;s.render.bake.cage_extrusion=.007;s.render.bake.max_ray_distance=.024;s.render.bake.margin=10;s.render.bake.normal_space='TANGENT'
jobs=[('bake',o.name) for o in targets]+[('render',v) for v in ['front','face','back','quarter']]+[('save','')]
first=True

def step():
 global first
 try:
  bpy.context.window.scene=s
  if not jobs:(OUT/'bake_done.txt').write_text('complete');return None
  job,name=jobs.pop(0);(OUT/'bake_progress.txt').write_text(job+' '+name)
  if job=='bake':
   o=s.objects[name];sources=[high] if o in [body,pouch] else [h for h in hardware if (h.matrix_world.translation.x>=0)==(o.matrix_world.translation.x>=0)]
   # Plate origins may be zero; selecting both sides is safe: separated surfaces are outside ray range.
   if o in plates:sources=hardware
   bpy.ops.object.select_all(action='DESELECT')
   for h in sources:h.hide_render=False;h.hide_set(False);h.select_set(True)
   o.select_set(True);bpy.context.view_layer.objects.active=o;s.render.bake.use_clear=first;bpy.ops.object.bake(type='NORMAL');first=False
   for h in sources:h.select_set(False);h.hide_render=True;h.hide_set(True)
   img.save()
  elif job=='render':
   mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
   target=Vector((0,0,.79)) if name=='face' else Vector((0,0,0));s.camera.location={'front':(0,-4,0),'face':(0,-4,.79),'back':(0,4,0),'quarter':(-3,-4,.65)}[name];s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=.47 if name=='face' else 2.15;s.render.filepath=str(OUT/('low_baked_'+name+'.png'));bpy.ops.render.render(write_still=True)
  else:
   img.pack();bpy.data.libraries.write(str(OUT/'goblin_low_detail_test.blend'),{s},fake_user=True,compress=True)
  return .1
 except Exception:(OUT/'bake_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1)
print('Shared body/pouch/backplate normal atlas baking scheduled.')
