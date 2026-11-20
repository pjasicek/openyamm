import bpy,math,json,traceback
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');OUT=ROOT/'detail_rebuild_01';s=bpy.data.scenes['Goblin - Complete Low Mesh Detail Test'];bpy.context.window.scene=s
old=s.objects['Goblin_Low_Body'];old.name='Goblin_FirstPass_7800';old.hide_render=True;old.hide_set(True)
body=s.objects['Goblin_Weighted_0.4'];body.name='Goblin_Low_Body';body.hide_render=False;body.hide_set(False)
pouch=s.objects['Goblin_Low_Pouch'];plates=[o for o in s.objects if o.name.startswith('Goblin_Low_BackPlate')];targets=[body,pouch]+plates
mat=bpy.data.materials['Goblin Low Body Pouch Plates Normal'];bs=mat.node_tree.nodes.get('Principled BSDF');normal=next(n for n in mat.node_tree.nodes if n.type=='NORMAL_MAP');img=bpy.data.images['Goblin_Low_DetailNormal_2048'];tex=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE');mat.node_tree.nodes.active=tex
for l in list(bs.inputs['Normal'].links):mat.node_tree.links.remove(l)
body.data.materials.clear();body.data.materials.append(mat)
bpy.ops.object.select_all(action='DESELECT')
for o in targets:
 o.select_set(True)
 for p in o.data.polygons:p.use_smooth=True
bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.006);bpy.ops.object.mode_set(mode='OBJECT')
high=s.objects['Goblin_DetailBake_DenseBody'];hardware=[o for o in s.objects if o.name.startswith('Goblin_DetailBake_') and o!=high]
# Adapt cage distance to the nearest dense surface. This covers decimation error without
# using an equally large ray offset around every small tooth and finger.
bvh=BVHTree.FromPolygons([high.matrix_world@v.co for v in high.data.vertices],[p.vertices[:] for p in high.data.polygons],all_triangles=False)
cages={};cage_report={}
for o in targets:
 cage=o.copy();cage.data=o.data.copy();cage.name='Goblin_BakeCage_'+o.name;s.collection.objects.link(cage);cage.hide_render=True;cage.hide_set(True);distances=[]
 for v in cage.data.vertices:
  offset=.006
  if o==body or o==pouch:
   point=o.matrix_world@v.co;hit=bvh.find_nearest(point)
   if hit[0] is not None:offset=.004+max(0,min(.025,(hit[0]-point).dot(v.normal)))
   if point.z>.70 and point.y<-.07:offset=min(offset,.007)
  v.co+=v.normal*offset;distances.append(offset)
 cages[o.name]=cage;cage_report[o.name]={'min_offset':min(distances),'max_offset':max(distances)}
(OUT/'cage_report.json').write_text(json.dumps(cage_report,indent=2))
s.render.bake.use_selected_to_active=True;s.render.bake.use_cage=True;s.render.bake.max_ray_distance=.06;s.render.bake.margin=10;s.render.bake.normal_space='TANGENT'
jobs=[('bake',o.name) for o in targets]+[('render',v) for v in ['front','face','back','quarter']]+[('save','')];first=True

def step():
 global first
 try:
  bpy.context.window.scene=s
  if not jobs:(OUT/'refined_done.txt').write_text('complete');return None
  job,name=jobs.pop(0);(OUT/'refined_progress.txt').write_text(job+' '+name)
  if job=='bake':
   o=s.objects[name];sources=[high] if o in [body,pouch] else hardware;bpy.ops.object.select_all(action='DESELECT')
   for h in sources:h.hide_render=False;h.hide_set(False);h.select_set(True)
   o.select_set(True);bpy.context.view_layer.objects.active=o;s.render.bake.cage_object=cages[o.name];s.render.bake.use_clear=first;bpy.ops.object.bake(type='NORMAL');first=False
   for h in sources:h.select_set(False);h.hide_render=True;h.hide_set(True)
   img.save()
  elif job=='render':
   mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal']);target=Vector((0,0,.79)) if name=='face' else Vector((0,0,0));s.camera.location={'front':(0,-4,0),'face':(0,-4,.79),'back':(0,4,0),'quarter':(-3,-4,.65)}[name];s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=.47 if name=='face' else 2.15;s.render.filepath=str(OUT/('refined_baked_'+name+'.png'));bpy.ops.render.render(write_still=True)
  else:
   img.pack();bpy.data.libraries.write(str(OUT/'goblin_low_detail_test.blend'),{s},fake_user=True,compress=True)
  return .1
 except Exception:(OUT/'refined_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print('Refined head and adaptive cage bake scheduled.')
