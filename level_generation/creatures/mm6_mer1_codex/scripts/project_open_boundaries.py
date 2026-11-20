"""Complete ray-bake texels by nearest surface on their matching source piece, with tangent-normal transport."""
import bpy,bmesh,json,numpy as np
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
AXES=[Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
def unit(v):return v/max(float(np.linalg.norm(v)),1e-12)
def linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def pixels(path):
 im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='Non-Color';return im,np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4)
def basis(me,loops,w):
 n=unit(sum(np.array(me.corner_normals[l].vector)*q for l,q in zip(loops,w)));t=sum(np.array(me.loops[l].tangent)*q for l,q in zip(loops,w));t=unit(t-n*(t@n));sgn=1 if sum(me.loops[l].bitangent_sign*q for l,q in zip(loops,w))>=0 else-1;return t,np.cross(n,t)*sgn,n

def complete(obj,high,source_tex,folder):
 lo=obj.data;hi=high.data
 if any(len(f.vertices)>4 for f in hi.polygons):
  bm=bmesh.new();bm.from_mesh(hi);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(hi);bm.free()
 for me in [lo,hi]:me.calc_loop_triangles();me.calc_tangents(uvmap=me.uv_layers.active.name)
 lowpart=[x.value for x in lo.attributes['piece'].data]if 'piece'in lo.attributes else[0]*len(lo.vertices);hipart=[x.value for x in hi.attributes['piece'].data]if 'piece'in hi.attributes else[0]*len(hi.vertices)
 ids={Counter(lowpart[i]for i in t.vertices).most_common(1)[0][0]for t in lo.loop_triangles};hi_co=[v.co.copy()for v in hi.vertices];trees={};triangles={}
 for pid in ids:
  keep={pid}
  for child,parent in [(14,0),(15,0),(16,10),(17,12)]:
   if pid==parent and child not in ids:keep.add(child)
  ts=[t for t in hi.loop_triangles if Counter(hipart[i]for i in t.vertices).most_common(1)[0][0]in keep];assert ts
  triangles[pid]=ts;trees[pid]=BVHTree.FromPolygons(hi_co,[tuple(t.vertices)for t in ts],all_triangles=True)
 source=[];temporary=[]
 for mi,textures in enumerate(source_tex):
  entry={}
  for key in ['basecolor','region_mask','metal_rough','material_classes']:
   im=textures[key]
   if im:
    file,pix=pixels(bpy.path.abspath(im.filepath));temporary.append(file);entry[key]=linear(pix[:,:,:3])if key=='basecolor'else pix[:,:,:3]
   else:entry[key]=None
  material=high.data.materials[mi];bs=material.node_tree.nodes.get('Principled BSDF');node=bs.inputs['Normal'].links[0].from_node;im=node.inputs['Color'].links[0].from_node.image;file,pix=pixels(bpy.path.abspath(im.filepath));temporary.append(file);entry['normal']=pix[:,:,:3];source.append(entry)
 def sample(arr,uv):
  if arr is None:return np.zeros(3)
  height,width=arr.shape[:2];x,y=np.clip(np.array(uv)*[width,height]-.5,[0,0],[width-1,height-1]);i,j=int(x),int(y);fx,fy=x-i,y-j
  return arr[j,i]*(1-fx)*(1-fy)+arr[j,min(i+1,width-1)]*fx*(1-fy)+arr[min(j+1,height-1),i]*(1-fx)*fy+arr[min(j+1,height-1),min(i+1,width-1)]*fx*fy
 outputs=[];report=[]
 for mi in range(len(obj.data.materials)):
  files={};data={}
  for key in ['basecolor','region_mask','metal_rough','normal','material_classes','coverage','uv_coverage']:
   files[key],data[key]=pixels(folder/f'{mi}_{key}.png')
  miss=(data['uv_coverage'][:,:,0]>.5)&(data['coverage'][:,:,0]<.5);outputs.append((files,data,miss));report.append({'material':mi,'missing_before':int(miss.sum()),'projected_texels':0,'max_projection_distance_m':0.,'pieces':{}})
 for t in lo.loop_triangles:
  mi=lo.polygons[t.polygon_index].material_index;files,data,miss=outputs[mi];N=miss.shape[0];loops=list(t.loops);vv=list(t.vertices);uv=np.array([lo.uv_layers.active.data[l].uv[:]for l in loops])*N;a,b,c=uv
  x0,y0=np.maximum(np.floor(uv.min(0)).astype(int),0);x1,y1=np.minimum(np.ceil(uv.max(0)).astype(int),N-1)
  if x1<x0 or y1<y0 or not miss[y0:y1+1,x0:x1+1].any():continue
  ys,xs=np.where(miss[y0:y1+1,x0:x1+1]);xs+=x0;ys+=y0;xx=xs+.5;yy=ys+.5;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-12:continue
  w0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den;w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;weights=np.c_[w0,w1,1-w0-w1];valid=(weights>=-.002).all(1);pid=Counter(lowpart[i]for i in vv).most_common(1)[0][0];co=np.array([lo.vertices[i].co[:]for i in vv])
  for x,y,w in zip(xs[valid],ys[valid],weights[valid]):
   point=Vector(w@co);loc,n,fi,d=trees[pid].find_nearest(point);assert loc is not None and d<.12,(pid,d);src=triangles[pid][fi];sv=list(src.vertices);sl=list(src.loops);sw=np.array(barycentric_transform(loc,*[hi_co[i]for i in sv],*AXES));suv=sum(np.array(hi.uv_layers.active.data[l].uv)*q for l,q in zip(sl,sw));sm=hi.polygons[src.polygon_index].material_index
   for key in ['basecolor','region_mask','metal_rough','material_classes']:
    color=sample(source[sm][key],suv);data[key][y,x,:3]=srgb(color)if key=='basecolor'else color
   st,sb,sn=basis(hi,sl,sw);normal=unit(sample(source[sm]['normal'],suv)*2-1);world=unit(st*normal[0]+sb*normal[1]+sn*normal[2]);lt,lb,ln=basis(lo,loops,w);data['normal'][y,x,:3]=unit(np.array([world@lt,world@lb,world@ln]))*.5+.5;data['coverage'][y,x,:3]=1;miss[y,x]=False;r=report[mi];r['projected_texels']+=1;r['max_projection_distance_m']=max(r['max_projection_distance_m'],float(d));r['pieces'][str(pid)]=r['pieces'].get(str(pid),0)+1
 for mi,(files,data,miss)in enumerate(outputs):
  for key,im in files.items():
   if key!='uv_coverage':im.pixels.foreach_set(data[key].ravel());im.filepath_raw=str(folder/f'{mi}_{key}.png');im.file_format='PNG';im.save()
   bpy.data.images.remove(im)
 for im in temporary:bpy.data.images.remove(im)
 (folder/'nearest_projection.json').write_text(json.dumps(report,indent=2));print('NEAREST PIECE PROJECTION',report,flush=True)
