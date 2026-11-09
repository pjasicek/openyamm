import bpy,bmesh,json,traceback
from mathutils import Vector
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/skirt_rebuild_01');s=bpy.data.scenes['Goblin - Rebuilt Skirt and Belt v2'];bpy.context.window.scene=s
body=s.objects['Goblin_CleanWaistCut'];covered=[o for o in s.objects if o.name.startswith('Goblin_CoveredAnatomy_')]
# Blend the covered torso volume in the same direction as the preserved waist.
torso=max(covered,key=lambda o:max(v.co.z for v in o.data.vertices));N=len(torso.data.vertices)//4
center=sum((v.co for v in torso.data.vertices[:N]),Vector())/N
for k,(oldscale,newscale) in enumerate([(1,1),(.97,1.018),(1.,1.035),(.9,.94)]):
 for v in torso.data.vertices[k*N:(k+1)*N]:
  v.co.x=center.x+(v.co.x-center.x)/oldscale*newscale;v.co.y=center.y+(v.co.y-center.y)/oldscale*newscale
# Join matching cut rings so vertex normals are continuous across the joins.
vs=[];fs=[]
for o in [body]+covered:
 offset=len(vs);vs.extend([v.co[:] for v in o.data.vertices]);fs.extend([[i+offset for i in p.vertices] for p in o.data.polygons]);o.hide_render=True;o.hide_set(True)
me=bpy.data.meshes.new('Goblin fitted body with shared seam normals');me.from_pydata(vs,[],fs);me.update();bm=bmesh.new();bm.from_mesh(me)
seams=[v for v in bm.verts if abs(v.co.z+.235)<1e-5 or abs(v.co.z-.213)<1e-5];bmesh.ops.remove_doubles(bm,verts=seams,dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
joined=bpy.data.objects.new('Goblin_Body_WithFittedWaist',me);s.collection.objects.link(joined);me.materials.append(body.data.materials[0])
for p in me.polygons:p.use_smooth=True
low=next(o for o in s.objects if o.name.startswith('Goblin_SkirtBelt_Low'));proxy=next(o for o in s.objects if o.name.startswith('Skirt_BakeSurface'));high=next(o for o in s.objects if o.name.startswith('Skirt_DenseBakeSource'));source=next(o for o in s.objects if o.name.startswith('SkirtStudy_Source200K'));pouch=s.objects['Goblin_PreservedPouch']
mat=low.data.materials[0];bs=mat.node_tree.nodes.get('Principled BSDF');normal=next(n for n in mat.node_tree.nodes if n.type=='NORMAL_MAP');img=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
for link in list(bs.inputs['Normal'].links):mat.node_tree.links.remove(link)
cage=proxy.copy();cage.data=proxy.data.copy();cage.name='Skirt_RadialBakeCage';s.collection.objects.link(cage)
for v in cage.data.vertices:
 radial=Vector((v.co.x,v.co.y,0));radial.normalize();v.co+=radial*.03
cage.hide_render=True;cage.hide_set(True)
s.render.bake.use_cage=True;s.render.bake.cage_object=cage;s.render.bake.max_ray_distance=.08
# Restore separately modeled back hardware unchanged in both comparison variants.
hardware=[]
for o in bpy.data.scenes['MM6 Goblin - Quad Remesh 200K'].objects:
 if o.type=='MESH' and ('Upper-back plate' in o.name or 'Back plate rivet' in o.name):
  cp=o.copy();cp.data=o.data;s.collection.objects.link(cp);cp.hide_render=False;cp.hide_viewport=False;cp.hide_set(False);hardware.append(cp)
visible_rebuilt=[joined,low,pouch]+hardware
jobs=['bake']+[(view,mode) for view in ['front','quarter','back'] for mode in ['source','unbaked','baked']]+['full','save']
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:(ROOT/'finished.txt').write_text('complete');return None
  job=jobs.pop(0);(ROOT/'progress.txt').write_text(str(job))
  if job=='bake':
   high.hide_set(False);high.hide_render=False;proxy.hide_set(False);proxy.hide_render=False;bpy.ops.object.select_all(action='DESELECT');high.select_set(True);proxy.select_set(True);bpy.context.view_layer.objects.active=proxy;bpy.ops.object.bake(type='NORMAL');img.save();high.hide_render=True;high.hide_set(True);proxy.hide_render=True;proxy.hide_set(True)
  elif job=='save':
   img.pack();source.hide_set(True);bpy.ops.object.select_all(action='DESELECT')
   for o in visible_rebuilt:o.hide_set(False);o.hide_viewport=False;o.hide_render=False;o.select_set(True)
   bpy.context.view_layer.objects.active=low
   bpy.ops.export_scene.gltf(filepath=str(ROOT/'goblin_skirt_rebuild_review.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False)
   bpy.data.libraries.write(str(ROOT/'skirt_rebuild.blend'),{s},fake_user=True,compress=True)
   report={'scene':s.name,'new_garment_triangles':len(low.data.polygons),'retained_and_repaired_body_triangles':sum(len(p.vertices)-2 for p in joined.data.polygons),'preserved_pouch_triangles':sum(len(p.vertices)-2 for p in pouch.data.polygons),'back_hardware_triangles':sum(len(p.vertices)-2 for o in hardware for p in o.data.polygons),'review_total_triangles':sum(len(p.vertices)-2 for o in visible_rebuilt for p in o.data.polygons),'normal_map':img.name,'normal_resolution':list(img.size),'note':'Component reconstruction test. Remaining body/pouch/hardware retain source-level density; not a final runtime LOD. Waist/upper thighs reconstructed under clothing and joined to original cut rings; rest of source geometry retained.'};(ROOT/'final_report.json').write_text(json.dumps(report,indent=2)+'\n')
  else:
   view,mode=('front','baked') if job=='full' else job
   source.hide_render=mode!='source'
   for o in [joined,low,pouch]:o.hide_render=mode=='source'
   for link in list(bs.inputs['Normal'].links):mat.node_tree.links.remove(link)
   if mode=='baked':mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
   cam=s.camera;offset={'front':(0,-4,0),'quarter':(-3,-4,.5),'back':(0,4,0)}[view];cam.location=Vector(offset);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.15 if job=='full' else .82;s.render.filepath=str(ROOT/('full_baked.png' if job=='full' else view+'_'+mode+'.png'));bpy.ops.render.render(write_still=True)
  return .1
 except Exception:(ROOT/'finish_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1)
print('Joined seams and queued corrected cage bake and comparisons.')
