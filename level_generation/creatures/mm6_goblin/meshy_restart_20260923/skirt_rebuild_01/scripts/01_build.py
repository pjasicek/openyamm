import bpy,bmesh,numpy as np,math,json,traceback
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/skirt_rebuild_01')
previous=bpy.context.scene
s=bpy.data.scenes.new('Goblin - Rebuilt Skirt and Belt v2');bpy.context.window.scene=s
src=bpy.data.scenes['MM6 Goblin - Quad Remesh 200K'].objects['Goblin_QR_200K_DensityGuided']
source=src.copy();source.data=src.data.copy();source.name='SkirtStudy_Source200K';s.collection.objects.link(source);source.hide_viewport=False;source.hide_render=False;source.hide_set(False)
for attr in list(source.data.color_attributes):source.data.color_attributes.remove(attr)
co=np.array([source.matrix_world@v.co for v in source.data.vertices]);polys=np.array([p.vertices[:] for p in source.data.polygons]);bvh=BVHTree.FromPolygons([Vector(v) for v in co],polys.tolist(),all_triangles=True)
# Front is negative Y. Columns refer to the measured cylindrical view, back -> right -> front -> left -> back.
edges=[0,43,78,112,148,185,223,270,326,397,455,501,539,576,611,646,685,720]
tip_rows=[239,222,224,229,230,230,239,257,263,257,238,226,231,229,223,225,238]
def angle(col):return (col/720*2-1)*math.pi
def direction(a):return Vector((math.sin(a),-math.cos(a),0))
def ray_r(a,z):
 d=direction(a);hit,n,idx,dist=bvh.ray_cast(Vector((0,0,z))+d*.33,-d,.33)
 return .33-dist if hit is not None else None
def smooth_radius(a,z):
 vals=[ray_r(a+da,z+dz) for da in [-.018,0,.018] for dz in [-.012,0,.012]];vals=[v for v in vals if v is not None]
 return float(np.quantile(vals,.30)) if vals else .16
# Belt surface is fitted below its loops and buckle so these can become map detail.
def belt_top(a):return .189-.015*math.cos(a)
def belt_bottom(a):return belt_top(a)-.057
verts=[];faces=[];uvfaces=[];mats=[];front_faces=[];panel_specs=[]
def addface(ids,uv,mat=0):
 faces.append(ids);uvfaces.append(uv);mats.append(mat)
 if mat==0:front_faces.append(len(faces)-1)
def add_panel(i):
 l=edges[i]+1.4;r=edges[i+1]-1.4;mid=(l+r)/2;a=angle(mid);tip=.23-tip_rows[i]/299*.49
 top=belt_bottom(a)+.007
 zs=[top,.052,-.065,tip+.029]
 # Keep the distinctive pointed end; top neck is slightly narrower.
 widths=[.86,1,1,1]
 points=[];us=[]
 for k,z in enumerate(zs):
  for j in range(3):
   col=mid+(j-1)*(r-l)/2*widths[k];aa=angle(col)
   rr=smooth_radius(aa,z)
   # Panels under the right-hip pouch follow the skirt, not the pouch bulge.
   if 103<col<203 and z>-.075:
    rr=min(rr,.191+(.05-z)*.05)
   points.append(direction(aa)*rr+Vector((0,0,z)));us.append((j/2,(z-tip)/(top-tip)))
 rr=smooth_radius(a,tip+.013);points.append(direction(a)*rr+Vector((0,0,tip)));us.append((.5,0))
 start=len(verts);verts.extend([tuple(p) for p in points]);verts.extend([tuple(p-direction(math.atan2(p.x,-p.y))*.004) for p in points])
 tile_x=i%9;tile_y=i//9;x0=.022+tile_x*.108;y0=.025+tile_y*.38
 def uv(idx):u,v=us[idx];return (x0+u*.094,y0+v*.345)
 fs=[]
 for k in range(3):
  for j in range(2):fs.append([k*3+j,k*3+j+1,(k+1)*3+j+1,(k+1)*3+j])
 fs.extend([[9,10,12],[10,11,12]])
 # Angular increasing cross down gives inward normal; reverse for exterior.
 for f in fs:
  f=f[::-1];addface([start+x for x in f],[uv(x) for x in f]);addface([start+13+x for x in f[::-1]],[(0,0)]*len(f),1)
 outline=[0,1,2,5,8,11,12,9,6,3]
 for k,j in zip(outline,outline[1:]+outline[:1]):addface([start+k,start+j,start+j+13,start+k+13],[(0,0)]*4,1)
 panel_specs.append({'index':i,'left_column':l,'right_column':r,'top':top,'tip':tip})
for i in range(17):add_panel(i)
# Belt: 48 segments, 2 vertical sections, shallow closed thickness.
N=48;start=len(verts);belt_r=[]
for inside in [False,True]:
 for k in range(3):
  for j in range(N+1):
   a=-math.pi+j/N*2*math.pi;top=belt_top(a);bot=belt_bottom(a);z=bot+(top-bot)*k/2
   # Query middle of belt and smooth around angular samples to avoid modeling every loop.
   vals=[ray_r(a+da,(top+bot)/2) for da in np.linspace(-.09,.09,9)];vals=[v for v in vals if v is not None];rr=float(np.quantile(vals,.2))-.002
   if inside:rr-=.005
   verts.append(tuple(direction(a)*rr+Vector((0,0,z))))
for k in range(2):
 for j in range(N):
  ids=[start+k*(N+1)+j,start+k*(N+1)+j+1,start+(k+1)*(N+1)+j+1,start+(k+1)*(N+1)+j]
  uv=[(.025+j/N*.95,.80+k/2*.14),(.025+(j+1)/N*.95,.80+k/2*.14),(.025+(j+1)/N*.95,.80+(k+1)/2*.14),(.025+j/N*.95,.80+(k+1)/2*.14)]
  addface(ids,uv);addface([x+3*(N+1) for x in ids[::-1]],[(0,0)]*4,1)
for k in [0,2]:
 for j in range(N):
  a=start+k*(N+1)+j;b=a+1;ids=[a,a+3*(N+1),b+3*(N+1),b]
  if k==0:ids.reverse()
  addface(ids,[(0,0)]*4,1)
# Create mesh and explicit UVs, triangulate once before baking.
def create(name,vs,fs,uvs,material_ids):
 m=bpy.data.meshes.new(name);m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);s.collection.objects.link(o);uv=m.uv_layers.new(name='SkirtUV')
 for p,coords,mi in zip(m.polygons,uvs,material_ids):
  p.material_index=mi;p.use_smooth=True
  for li,xy in zip(p.loop_indices,coords):uv.data[li].uv=xy
 return o
low=create('Goblin_SkirtBelt_Low',verts,faces,uvfaces,mats)
# The original surface is a fused shell. Remove its clothing shell only, retaining deeper body and pouch.
c=co[polys].mean(axis=1);aa=np.arctan2(c[:,0],-c[:,1]);cols=(aa/math.pi+1)*360;rr=np.linalg.norm(c[:,:2],axis=1);zz=c[:,2]
remove=np.zeros(len(c),bool)
for idx,(a,col,r,z) in enumerate(zip(aa,cols,rr,zz)):
 if z>belt_top(a)+.005 or z<-.23 or r>.29:continue
 # Preserve the original right-side pouch.
 if c[idx,0]<-.213 and -.092<z<.125 and abs(c[idx,1])<.145:continue
 pi=min(16,max(0,np.searchsorted(edges,col)-1));sp=panel_specs[pi]
 if z>=belt_bottom(a)-.006:
  if z>=belt_bottom(a)-.006:remove[idx]=True
 elif z>=sp['tip']-.008:
  expected=smooth_radius(a,z)
  if 103<col<203 and z>-.075:expected=min(expected,.191+(.05-z)*.05)
  if r>expected-.034:remove[idx]=True
body=source.copy();body.data=source.data.copy();body.name='Goblin200K_ClothingShellRemoved';s.collection.objects.link(body)
bm=bmesh.new();bm.from_mesh(body.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in np.flatnonzero(remove)],context='FACES');bm.to_mesh(body.data);bm.free();body.data.update()
# A simple inner leather band closes the unseen waist cut under the new belt/strip roots.
vs=[];fs=[]
for z in [-.08,.13,.214]:
 for j in range(32):
  a=j/32*2*math.pi;vs.append((.147*math.sin(a),.037-.099*math.cos(a),z))
for k in range(2):
 for j in range(32):fs.append((k*32+j,k*32+(j+1)%32,(k+1)*32+(j+1)%32,(k+1)*32+j))
under=create('Goblin_InnerWaist_Band',vs,fs,[[(0,0)]*4 for f in fs],[0]*len(fs))
underlegs=[]
for side in [-1,1]:
 vs=[];fs=[]
 for z in [-.245,-.14,-.03,.095]:
  for j in range(20):
   a=j/20*2*math.pi;vs.append((side*.105+.084*math.sin(a),.029-.096*math.cos(a),z))
 for k in range(3):
  for j in range(20):fs.append((k*20+j,k*20+(j+1)%20,(k+1)*20+(j+1)%20,(k+1)*20+j))
 underlegs.append(create('Goblin_HiddenUpperThigh_'+str(side),vs,fs,[[(0,0)]*4 for f in fs],[0]*len(fs)))
# Materials: front gets baked normal; inward/thickness surfaces retain a neutral flat normal.
plain=bpy.data.materials.new('Skirt study clay');plain.use_nodes=True;bs=plain.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.34,.36,1);bs.inputs['Roughness'].default_value=.7
for ob in underlegs:ob.data.materials.append(plain)
mat=plain.copy();mat.name='Skirt study baked';low.data.materials.append(mat);low.data.materials.append(plain);under.data.materials.append(plain);body.data.materials.clear();body.data.materials.append(plain);source.data.materials.clear();source.data.materials.append(plain)
bpy.context.view_layer.objects.active=low;bpy.ops.object.select_all(action='DESELECT');low.select_set(True);mod=low.modifiers.new('Freeze bake triangulation','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
# Split outer/inner seams so bake and rendered surface share the same tangent normals.
edge_mats={e.key:set() for e in low.data.edges}
for p in low.data.polygons:
 for key in p.edge_keys:edge_mats[tuple(sorted(key))].add(p.material_index)
for e in low.data.edges:
 if len(edge_mats[e.key])>1:e.use_edge_sharp=True
mod=low.modifiers.new('Separate thin-edge normals','EDGE_SPLIT');mod.use_edge_angle=False;mod.use_edge_sharp=True;bpy.ops.object.modifier_apply(modifier=mod.name)
# Bake only outward faces; inside faces must not write over the exterior UV islands.
m=low.data;front=[p for p in m.polygons if p.material_index==0];proxy=create('Skirt_BakeSurface',[v.co[:] for v in m.vertices],[p.vertices[:] for p in front],[[m.uv_layers.active.data[li].uv[:] for li in p.loop_indices] for p in front],[0]*len(front));proxy.data.materials.append(mat)
img=bpy.data.images.new('GoblinSkirt_Normal_2048',width=2048,height=2048,alpha=False);img.colorspace_settings.name='Non-Color';img.generated_color=(.5,.5,1,1);img.filepath_raw=str(ROOT/'skirt_normal.png');img.file_format='PNG'
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;mat.node_tree.nodes.active=node;normal=mat.node_tree.nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(node.outputs['Color'],normal.inputs['Color'])
# Dense original is used for baking; all originals remain untouched.
hsrc=bpy.data.scenes['MM6 Goblin - Quad Remesher Trial 01'].objects['Goblin_QR_Source_DensityGuided'];high=hsrc.copy();high.name='Skirt_DenseBakeSource';s.collection.objects.link(high);high.hide_viewport=False;high.hide_render=False;high.hide_set(False)
source.hide_render=True;source.hide_set(True);proxy.hide_render=True;body.hide_render=False
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=True;s.render.bake.use_selected_to_active=True;s.render.bake.cage_extrusion=.026;s.render.bake.max_ray_distance=.07;s.render.bake.margin=10;s.render.bake.normal_space='TANGENT'
cd=bpy.data.cameras.new('Skirt comparison camera');cam=bpy.data.objects.new('Skirt comparison camera',cd);s.collection.objects.link(cam);s.camera=cam;cd.type='ORTHO';cd.ortho_scale=.82
s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX'
s.world=bpy.data.worlds.new('Skirt study world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.15,.17,.20,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
for name,offset,power,size in [('Key',(-3,-4,5),650,3),('Fill',(4,-2,2),400,4),('Rim',(1,3,4),800,3)]:
 ld=bpy.data.lights.new('Skirt '+name,'AREA');ld.energy=power;ld.size=size;ob=bpy.data.objects.new('Skirt '+name,ld);s.collection.objects.link(ob);ob.location=offset;ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
report={'scene':s.name,'removed_source_triangles':int(remove.sum()),'remaining_source_triangles':len(body.data.polygons),'replacement_skirt_belt_triangles':len(low.data.polygons),'inner_band_triangles':sum(len(p.vertices)-2 for ob in [under]+underlegs for p in ob.data.polygons),'panels':panel_specs,'note':'First fitted construction and bake test. Original meshes unchanged; cut body is a separate copy. Need inspect gaps and pouch seam.'};(ROOT/'construction_report.json').write_text(json.dumps(report,indent=2)+'\n')
jobs=['bake']+[(view,mode) for view in ['front','quarter','back'] for mode in ['source','unbaked','baked']]+['save']
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:
   bpy.context.window.scene=previous;(ROOT/'done.txt').write_text('complete');return None
  job=jobs.pop(0);(ROOT/'progress.txt').write_text(str(job))
  if job=='bake':
   proxy.hide_render=False
   bpy.ops.object.select_all(action='DESELECT');high.select_set(True);proxy.select_set(True);bpy.context.view_layer.objects.active=proxy;bpy.ops.object.bake(type='NORMAL');img.save();high.hide_render=True;high.hide_set(True);proxy.hide_render=True;proxy.hide_set(True)
  elif job=='save':
   img.pack();bpy.data.libraries.write(str(ROOT/'skirt_rebuild_v2.blend'),{s},fake_user=True,compress=True)
  else:
   view,mode=job
   for ob in underlegs:ob.hide_render=mode=='source'
   source.hide_render=mode!='source';body.hide_render=mode=='source';low.hide_render=mode=='source';under.hide_render=mode=='source'
   bs=mat.node_tree.nodes.get('Principled BSDF')
   for link in list(bs.inputs['Normal'].links):mat.node_tree.links.remove(link)
   if mode=='baked':mat.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
   offset={'front':(0,-4,0),'quarter':(-3,-4,.5),'back':(0,4,0)}[view];cam.location=Vector(offset);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(ROOT/(view+'_'+mode+'.png'));bpy.ops.render.render(write_still=True)
  return .1
 except Exception:
  (ROOT/'error.txt').write_text(traceback.format_exc());bpy.context.window.scene=previous;return None
bpy.app.timers.register(step,first_interval=.1)
print(json.dumps(report))
