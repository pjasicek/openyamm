"""Nearest-surface bake restricted to matching material and surface direction."""
import bpy,bmesh,sys,json,subprocess,math,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import round4_search as S
W=P/'work/round5';R=P/'review/round5';config=json.loads((W/'config.json').read_text());step=config.get('step',6);dest=W/f'baked{step}';dest.mkdir(exist_ok=True)
def norm(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-12)
def lin(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def srgb(c):return np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
def geometry(ob):
 me=ob.data;me.calc_loop_triangles();me.calc_tangents(uvmap=me.uv_layers.active.name);tri=list(me.loop_triangles);vid=np.array([t.vertices for t in tri]);loops=np.array([t.loops for t in tri]);co=np.array([tuple(v.co)for v in me.vertices]);uv=np.array([tuple(x.uv)for x in me.uv_layers.active.data]);n=np.array([tuple(x.vector)for x in me.corner_normals]);t=np.array([tuple(x.tangent)for x in me.loops]);s=np.array([x.bitangent_sign for x in me.loops]);pieces=np.array([x.value for x in me.attributes['piece'].data])if me.attributes.get('piece')else np.zeros(len(co),int);keys=[(ob.data.materials[x.material_index].name.split('.')[0],int(np.bincount(pieces[v]).argmax()))for x,v in zip(tri,vid)];trees={}
 for key in sorted(set(keys)|{(k[0],-1)for k in keys}|{('*',-1)}|{('*',k[1])for k in keys}):
  ids=np.array([i for i,k in enumerate(keys)if (key[0]=='*'or k[0]==key[0])and(key[1]==-1 or k[1]==key[1])]);trees[key]=(BVHTree.FromPolygons(co.tolist(),vid[ids].tolist(),all_triangles=True),ids)
 weights=np.zeros((len(co),len(ob.vertex_groups)))
 for vert in me.vertices:
  for g in vert.groups:weights[vert.index,g.group]=g.weight
 guide=me.uv_layers.get('SourceUV')or me.uv_layers.active;source_uv=np.array([x.uv[:]for x in guide.data])[loops]
 return dict(source_uv=source_uv,bone_names=[g.name for g in ob.vertex_groups],weights=weights[vid],xyz=co[vid],uv=uv[loops],normal=n[loops],tangent=t[loops],sign=s[loops],keys=keys,trees=trees)
def basis(n,t,sgn):
 n=norm(n);t=norm(t-n*np.sum(n*t,axis=-1,keepdims=True));b=norm(np.cross(n,t))*np.where(sgn[:,None]<0,-1,1);return n,t,b
def bary(p,tri):
 e0=tri[:,1]-tri[:,0];e1=tri[:,2]-tri[:,0];d=p-tri[:,0];a=np.sum(e0*e0,1);b=np.sum(e0*e1,1);c=np.sum(e1*e1,1);q=np.sum(d*e0,1);r=np.sum(d*e1,1);den=np.maximum(a*c-b*b,1e-20);u=(c*q-b*r)/den;v=(a*r-b*q)/den;return np.stack([1-u-v,u,v],1)
def facing_hits(tree,points,normals,project=False):
 result=[]
 for p,n in zip(points,normals):
  h=tree.find_nearest(tuple(p))
  if project:
   ray=tree.ray_cast(Vector(p)+Vector(n)*.01,-Vector(n),.03)
   if ray[0]is not None and np.dot(ray[1],n)>.3 :h=(ray[0],ray[1],ray[2],float((ray[0]-Vector(p)).length))
  if np.dot(h[1],n)<.3:
   choices=[x for x in tree.find_nearest_range(tuple(p),max(.035,h[3]+.015))if np.dot(x[1],n)>.3]
   if choices:h=min(choices,key=lambda x:x[3])
  result.append(h)
 return result
def sample(im,uv):
 h,w=im.shape[:2];x=np.clip(uv[:,0]*w-.5,0,w-1);y=np.clip((1-uv[:,1])*h-.5,0,h-1);ix=x.astype(int);iy=y.astype(int);jx=np.minimum(ix+1,w-1);jy=np.minimum(iy+1,h-1);fx=(x-ix)[:,None];fy=(y-iy)[:,None];return (im[iy,ix]*(1-fx)+im[iy,jx]*fx)*(1-fy)+(im[jy,ix]*(1-fx)+im[jy,jx]*fx)*fy
# Unit checks: barycentric interpolation and the tangent frame round trip.
a=np.array([[[0.,0,0],[1.,0,0],[0,1.,0]]]);assert np.allclose(bary(np.array([[.2,.3,0]]),a),[[.5,.2,.3]])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4_before/work/export_reimport.blend'));S.reset();high={name:geometry(bpy.data.objects[name])for name in ['Body','Axe']};maps=dict(np.load(W/'source_maps.npz'))
for k in list(maps):
 if k.endswith('_base'):maps[k]=lin(maps[k])
bpy.ops.wm.open_mainfile(filepath=str(W/f'step{step}.blend'));S.reset();receipts={};bpy.context.scene.tool_settings.mesh_select_mode=(False,False,True);bpy.context.scene.tool_settings.use_uv_select_sync=True
for name in ['Body','Axe']:
 ob=bpy.data.objects[name];src=high[name];ob.data.normals_split_custom_set([(0.,0.,0.)]*len(ob.data.loops));ob.data.update();pv=[x.value for x in ob.data.attributes['piece'].data]if ob.data.attributes.get('piece')else[0]*len(ob.data.vertices);seen=set();moves=[];vn={vi:np.array(ob.data.corner_normals[li].vector)for f in ob.data.polygons for li,vi in zip(f.loop_indices,f.vertices)}
 for face in ob.data.polygons:
  mat=ob.data.materials[face.material_index].name.split('.')[0]
  for vi in face.vertices:
   if vi in seen:continue
   seen.add(vi);tree,ids=src['trees'][mat,-1];hit=facing_hits(tree,[ob.data.vertices[vi].co],[vn[vi]])[0];moves.append(hit[3])
 if name=='Body':
  tree,ids=src['trees']['*',0];changed=[]
  for v in ob.data.vertices:
   if pv[v.index]!=0:continue
   loc,normal,fi,d=tree.find_nearest(v.co)
   if d<1e-5:continue
   si=ids[fi];sw=bary(np.array([loc]),src['xyz'][si:si+1])[0];sw=np.maximum(sw,0);sw/=sw.sum();weights=sw@src['weights'][si]
   v.co=loc
   for g in list(v.groups):
    if ob.vertex_groups[g.group].name!='_reduction_protect':ob.vertex_groups[g.group].remove([v.index])
   keep=np.argsort(weights)[-8:];total=weights[keep].sum()
   for j in keep:
    if weights[j]>1e-8:ob.vertex_groups[src['bone_names'][j]].add([v.index],float(weights[j]/total),'REPLACE')
   changed.append(d)
  print('HEAD_SURFACE_REFIT',len(changed),max(changed,default=0),flush=True)
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges));bm.to_mesh(ob.data);bm.free();ob.data.normals_split_custom_set([(0.,0.,0.)]*len(ob.data.loops));ob.data.update();guide=ob.data.uv_layers.new(name='SourceUV');original=ob.data.uv_layers['UVMap'];
 for a,b in zip(guide.data,original.data):a.uv=b.uv
 ob.data.uv_layers.active=original;original.active_render=True;bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 for slot in sorted(set(f.material_index for f in ob.data.polygons)):
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
  for face in ob.data.polygons:face.select=face.material_index==slot
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.object.mode_set(mode='OBJECT')
  # Smart projection can fold a few curved charts. Split only those triangles, then repack all islands.
  for attempt in range(6):
   me=ob.data;me.calc_loop_triangles();uv=me.uv_layers.active.data;owner=np.full((1024,1024),-1,int);bad=set()
   for tri in me.loop_triangles:
    if tri.material_index!=slot:continue
    p=np.array([uv[i].uv[:]for i in tri.loops])*1024;lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),1023);a,b,c=p;det=np.linalg.det(np.stack([b-a,c-a]))
    if abs(det)<1e-10:bad.add(tri.polygon_index);continue
    x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);u=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/det;v=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/det;m=(u>1e-6)&(v>1e-6)&(u+v<1-1e-6);yy,xx=np.where(m);yy+=lo[1];xx+=lo[0];old=owner[yy,xx];bad.update(old[old>=0].tolist())
    if np.any(old>=0):bad.add(tri.polygon_index)
    owner[yy,xx]=tri.polygon_index
   if not bad:break
   for j,fi in enumerate(sorted(bad)):
    face=me.polygons[fi];assert len(face.vertices)==3;xyz=np.array([me.vertices[i].co[:]for i in face.vertices]);e=xyz[1]-xyz[0];t=e/np.linalg.norm(e);n=np.cross(e,xyz[2]-xyz[0]);n/=max(np.linalg.norm(n),1e-12);b=np.cross(n,t);flat=np.stack([(xyz-xyz[0])@t,(xyz-xyz[0])@b],1);old=np.array([uv[i].uv[:]for i in face.loop_indices]);old_area=abs(np.linalg.det(np.stack([old[1]-old[0],old[2]-old[0]])));new_area=abs(np.linalg.det(np.stack([flat[1]-flat[0],flat[2]-flat[0]])));flat*=math.sqrt(max(old_area,1e-8)/max(new_area,1e-12))
    for li,p in zip(face.loop_indices,flat):uv[li].uv=(p[0]+10+j*2,p[1]+10)
   bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.pack_islands(rotate=True,margin=.003);bpy.ops.object.mode_set(mode='OBJECT');print('UV_CHART_REPAIR',name,slot,attempt,len(bad),flush=True)
  else:raise AssertionError('UV chart repair did not converge')
 print('SOURCE_DISTANCE',name,np.percentile(moves,[99,100]).tolist(),flush=True)
for name in ['Body','Axe']:
 ob=bpy.data.objects[name];src=high[name];low=geometry(ob);N=1024;output={};coverage={};distances=[]
 for material,_ in set(low['keys']):
  output[material]={mode:np.zeros((N,N,4 if mode=='mask'else 3),np.float32)for mode in ['base','orm','mask','normal']};coverage[material]=np.zeros((N,N),np.uint8)
 for ti,key in enumerate(low['keys']):
  material,piece=key;uv=low['uv'][ti].copy();uv[:,1]=1-uv[:,1];uv*=N;lo=np.maximum(np.floor(uv.min(0)).astype(int),0);hi=np.minimum(np.ceil(uv.max(0)).astype(int),N-1)
  if np.any(hi<lo):continue
  x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=uv;det=np.linalg.det(np.stack([b-a,c-a]));
  if abs(det)<1e-12:continue
  u=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/det;v=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/det;m=(u>1e-6)&(v>1e-6)&(u+v<1-1e-6);yy,xx=np.where(m);yy+=lo[1];xx+=lo[0];weights=np.stack([1-u[m]-v[m],u[m],v[m]],1)
  if not len(weights):continue
  pts=weights@low['xyz'][ti]
  tree,ids=src['trees']['*',-1];hits=[]
  for p,n in zip(pts,norm(weights@low['normal'][ti])):
   h=tree.find_nearest(tuple(p));ray=tree.ray_cast(Vector(p)+Vector(n)*.01,-Vector(n),.03)
   if ray[0]is not None and np.dot(ray[1],n)>.3:
    source_piece=src['keys'][ids[ray[2]]][1]
    if source_piece>=14 or h[3]>1e-5:h=(ray[0],ray[1],ray[2],float((ray[0]-Vector(p)).length))
   hits.append(h)
  positions=np.array([h[0]for h in hits]);si=ids[[h[2]for h in hits]];distances.extend(h[3]for h in hits)
  sw=bary(positions,src['xyz'][si]);suv=np.einsum('ni,nij->nj',sw,src['uv'][si]);sn,st,sb=basis(np.einsum('ni,nij->nj',sw,src['normal'][si]),np.einsum('ni,nij->nj',sw,src['tangent'][si]),np.einsum('ni,ni->n',sw,src['sign'][si]));tn,tt,tb=basis(weights@low['normal'][ti],weights@low['tangent'][ti],weights@low['sign'][ti]);coverage[material][yy,xx]+=1
  for mode in ['base','orm','mask','normal']:
   source_materials=np.array([src['keys'][i][0]for i in si]);val=np.empty((len(si),4 if mode=='mask'else 3))
   for source_material in set(source_materials):
    pick=source_materials==source_material;val[pick]=sample(maps[source_material+'_'+mode],suv[pick])
   if mode=='base':val=srgb(val)
   if mode=='normal':
    z=norm(val*2-1);world=norm(st*z[:,0,None]+sb*z[:,1,None]+sn*z[:,2,None]);val=(norm(np.stack([np.sum(world*tt,1),np.sum(world*tb,1),np.sum(world*tn,1)],1))+1)/2
   output[material][mode][yy,xx]=val
 for material,channels in output.items():
  np.savez_compressed(dest/f'{material}_projection.npz',coverage=coverage[material],**channels)
  receipts[material]={'covered_texels':int((coverage[material]>0).sum()),'overlap_texels':int((coverage[material]>1).sum()),'projection_distance_p99_max_m':np.percentile(distances,[99,100]).tolist()};assert receipts[material]['overlap_texels']==0
  print('PROJECTED',step,material,receipts[material],flush=True)
subprocess.run(['/usr/bin/python3',str(P/'scripts/round5_save_bake.py'),str(step)],check=True)
for name in ['Body','Axe']:
 me=bpy.data.objects[name].data;me.uv_layers.remove(me.uv_layers['SourceUV'])
# Bind the rebaked shared maps; tier previews are derived separately from the unchanged ramps.
for ob in [bpy.data.objects['Body'],bpy.data.objects['Axe']]:
 for slot in ob.material_slots:
  if not slot.material:continue
  mat=slot.material.copy();slot.material=mat;name=mat.name.split('.')[0];nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');bs=nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Metallic'].default_value=0;mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
  for mode in ['base','orm','normal']:
   path=dest/f'{name}_{mode}.png'
   if not path.exists():continue
   im=bpy.data.images.load(str(path));im.colorspace_settings.name='sRGB'if mode=='base'else'Non-Color';tex=nodes.new('ShaderNodeTexImage');tex.image=im
   if mode=='base':mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);nodes.active=tex
   elif mode=='orm':
    sep=nodes.new('ShaderNodeSeparateColor');mat.node_tree.links.new(tex.outputs['Color'],sep.inputs['Color']);mat.node_tree.links.new(sep.outputs['Green'],bs.inputs['Roughness'])
   else:
    nm=nodes.new('ShaderNodeNormalMap');mat.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest/'candidate.blend'))
(dest/'receipt.json').write_text(json.dumps({'source':'work/round4_before/work/export_reimport.blend','method':'Material/piece/facing-constrained cage projection, nearest-surface fallback for missed rays; accepted detailed surface normals plus original detail normal in reduced MikkTSpace','sets_1k':True,'maps':['base','mask','orm','normal'],'materials':receipts},indent=2)+'\n')
