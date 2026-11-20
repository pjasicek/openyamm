import bpy,bmesh,sys,json,subprocess,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
from reduction_render import render
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_lod0.blend'));C.activate('Standing',0);o=bpy.data.objects['Body'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();tree=BVHTree.FromPolygons([v.co.copy()for v in mm.vertices],[f.vertices[:]for f in mm.polygons]);ev.to_mesh_clear();rows=[]
fields=np.load(P/'work/inside_field.npz')
for cutcount in [5,10,20]:
 factor=1.
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/lod3_feet.blend'));C.activate('Standing',0);r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;oldn=len(me.vertices);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();posed=[v.co.copy()for v in mm.vertices];ev.to_mesh_clear();pv=np.array([x.value for x in me.attributes['piece'].data]);ranked=[]
 for e in me.edges:
  a,b=e.vertices
  if pv[a]<1000 or pv[b]<1000:continue
  score=0
  for t in [.25,.5,.75]:
   q=posed[a].lerp(posed[b],t)
   for vi in range(8):
    angle=vi*math.pi/4;h=Vector((math.cos(angle),math.sin(angle),0));ppm=700/1.7129090557573363;x=410+q.dot(h)*ppm;y=410-(q.z-.85)*ppm;ix,iy=int(x),int(y)
    if not(0<=ix<820 and 0<=iy<820)or fields[f'mask{vi}'][iy,ix]:continue
    ny,nx=fields[f'nearest{vi}'][:,iy,ix];score+=math.hypot(float(nx)+.5-x,float(ny)+.5-y)
  if score>0:ranked.append((score,int(a),int(b)))
 ranked.sort(reverse=True);print('RANKED_EDGES',ranked[:cutcount],flush=True);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();edges=[]
 for score,a,b in ranked[:cutcount]:edges.append(next(e for e in bm.verts[a].link_edges if bm.verts[b]in e.verts))
 existing={tuple(v.co)for v in bm.verts};bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=False);bm.verts.index_update();newids=[v.index for v in bm.verts if tuple(v.co)not in existing];assert len(newids)==cutcount,(cutcount,newids);print("NEWIDS",oldn,newids,flush=True);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();pos=[v.co.copy()for v in mm.vertices];ev.to_mesh_clear();gn={g.index:g.name for g in o.vertex_groups}
 for idx in newids:
  v=me.vertices[idx]
  p=pos[v.index];q=p.copy()
  for it in range(100):
   delta=Vector();count=0
   for vi in range(8):
    angle=vi*math.pi/4;h=Vector((math.cos(angle),math.sin(angle),0));ppm=700/1.7129090557573363;x=410+q.dot(h)*ppm;y=410-(q.z-.85)*ppm;ix,iy=int(x),int(y)
    if not(0<=ix<820 and 0<=iy<820)or fields[f'mask{vi}'][iy,ix]:continue
    ny,nx=fields[f'nearest{vi}'][:,iy,ix];delta+=h*((float(nx)+.5-x)/ppm)+Vector((0,0,(y-float(ny)-.5)/ppm));count+=1
   if not count:break
   q+=delta/count*.65
  delta=(q-p)*factor;print("CLIP_DELTA",v.index,delta[:],flush=True);M=np.zeros((3,3))
  for g in v.groups:
   if gn[g.group]in r.data.bones:M+=np.array((r.pose.bones[gn[g.group]].matrix@r.data.bones[gn[g.group]].matrix_local.inverted()).to_3x3())*g.weight
  v.co+=Vector(np.linalg.solve(M,np.array(delta)))
 me.update();C.reset();tag=f'edgeclip{cutcount}';dest=P/f'work/lod3_{tag}.blend';tri=C.triangles(o);assert tri<=1290,tri;bpy.ops.wm.save_as_mainfile(filepath=str(dest));out=P/f'review/reduction/lod3_{tag}';render(dest,out,P/'work/reduction/lod3_continuous',88)
 v=json.loads(subprocess.check_output(['/usr/bin/python3','-B',str(P/'scripts/reduction_metrics.py'),str(P/'review/reduction/lod3_reference'),str(out)],text=True));rr=list(v['views'].values());uu=[(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rr];pooled=sum(x['iou']*u for x,u in zip(rr,uu))/sum(uu);rows.append({'edges':cutcount,'triangles':tri,'pooled_iou':pooled,'visual':v});(P/'review/reduction/edgeclip_curve.json').write_text(json.dumps(rows,indent=2));print('EDGECLIP',cutcount,tri,pooled,flush=True)
 if pooled>=.97:break
