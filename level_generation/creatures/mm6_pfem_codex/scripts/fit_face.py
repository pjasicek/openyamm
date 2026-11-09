import bpy,bmesh,sys,json,numpy as np,math
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
body=bpy.data.objects['Body'];me=body.data
pv=np.array([v.value for v in me.attributes['piece'].data]);co=np.array([tuple(v.co) for v in me.vertices])
our=co[(pv==1)&(co[:,1]<-.045)&(co[:,2]>1.425)&(co[:,2]<1.57)]
nose=our[np.argmin(our[:,1])];top=co[pv==2,2].max()
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p/'meshy/head_model_v1/model_urls_glb.glb'))
hm=next(o for o in set(bpy.data.objects)-before if o.type=='MESH')
mc=np.array([tuple(hm.matrix_world@v.co) for v in hm.data.vertices]);hm.data.calc_loop_triangles()
tri=[tuple(f.vertices) for f in hm.data.loop_triangles]
band=mc[(mc[:,2]>.05)&(mc[:,2]<.35)];mn=band[band[:,1].argmin()]
scale=(top-nose[2])/(mc[:,2].max()-mn[2])
T=np.eye(4);T[:3,:3]*=scale;T[:3,3]=nose-scale*mn
print('INIT',scale,nose,mn)
def ume(A,B):
 ma,mb=A.mean(0),B.mean(0);a,b=A-ma,B-mb
 U,S,Vt=np.linalg.svd(b.T@a/len(A));D=np.eye(3);D[2,2]=np.sign(np.linalg.det(U@Vt))
 R=U@D@Vt;sc=np.trace(np.diag(S)@D)/(a*a).sum(1).mean()
 M=np.eye(4);M[:3,:3]=sc*R;M[:3,3]=mb-sc*R@ma;return M
for it in range(25):
 pc=mc@T[:3,:3].T+T[:3,3];tree=BVHTree.FromPolygons([Vector(x) for x in pc],tri)
 near=np.array([tuple(tree.find_nearest(Vector(x))[0]) for x in our]);d=np.linalg.norm(near-our,axis=1)
 keep=d<np.percentile(d,75);T=ume(near[keep],our[keep])@T
print('ICP mm',np.sqrt(np.mean(d[keep]**2))*1000,'scale',np.cbrt(np.linalg.det(T[:3,:3])))
json.dump({'matrix':T.tolist(),'rms_mm':float(np.sqrt(np.mean(d[keep]**2))*1000)},open(p/'work/face_align.json','w'),indent=2)
pc=mc@T[:3,:3].T+T[:3,3];tree=BVHTree.FromPolygons([Vector(x) for x in pc],tri)
# Smooth the corrupted eyelid/lip topology tangentially, then project the front surface onto the clean reconstruction.
bm=bmesh.new();bm.from_mesh(me);layer=bm.verts.layers.int['piece']
def weight(v):
 x,y,z=v.co
 if v[layer]!=1 or y>-.035:return 0.
 e=math.hypot((x+.007)/.085,(z-1.493)/.080)
 return min(1,max(0,(1-e)/.22))
for _ in range(4):
 updates={}
 for v in bm.verts:
  w=weight(v)
  if w and not v.is_boundary:
   avg=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges)
   updates[v]=v.co.lerp(avg,.18*w)
 for v,x in updates.items():v.co=x
moved=0;maxd=0.
for v in bm.verts:
 w=weight(v)
 if not w:continue
 hit,n,idx,d=tree.ray_cast(Vector((v.co.x,-.4,v.co.z)),Vector((0,1,0)),.5)
 if hit is None:continue
 dv=(hit-v.co)*w
 if dv.length>.014:dv*=.014/dv.length
 v.co+=dv;moved+=1;maxd=max(maxd,dv.length)
edges=[e for e in bm.edges if e.is_boundary and all(v[layer]==1 and v.co.z>1.40 for v in e.verts)]
caps=[]
unused=set(edges)
while unused:
 e=unused.pop();loop=list(e.verts);last=loop[-1]
 while last!=loop[0]:
  next_e=next((a for a in last.link_edges if a in unused),None)
  if next_e is None:break
  unused.remove(next_e);last=next_e.other_vert(last)
  if last!=loop[0]:loop.append(last)
 if last!=loop[0]:raise RuntimeError('Open face boundary')
 caps.append(bm.faces.new(loop))
print('FINAL face caps',len(caps))
for face in caps:face.material_index=3;face.smooth=True
bmesh.ops.triangulate(bm,faces=caps)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
print('FIT',moved,maxd)
for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
me.attributes['orig_co'].data.foreach_set('vector',np.array([tuple(v.co) for v in me.vertices]).ravel())
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/fitted_head'),1.49,.35,views=('front','left','three_quarter'),resolution=(600,600))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
body.data.materials.clear();mat=bpy.data.materials.new('RigPreview');mat.use_nodes=True
im=bpy.data.images.new('RigPreview',width=8,height=8);im.generated_color=(.7,.7,.7,1)
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
for f in me.polygons:f.material_index=0
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
