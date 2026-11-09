"""Pose-estimation retry: wider A-pose, bottom-centred, one opaque material/primitive. Preserve v1."""
import bpy,sys,os,json,math,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/kept_m_clean_v1.blend'))
body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);before=co.copy()
parts=np.array([a.value for a in me.attributes['piece'].data])
for sg in (-1,1):
 pivot=Vector((sg*.20,.025,1.33));rotation=Matrix.Rotation(math.radians(-sg*20),3,'Y')
 for v in me.vertices:
  if v.co.x*sg<=0:continue
  if parts[v.index] in (3,4):w=1.0
  elif parts[v.index]==0 and (v.co.z>1.06 or abs(v.co.x)>.25):
   w=min(1,max(0,(v.co.x*sg-.12)/.16));w=w*w*(3-2*w)
  else:w=0.0
  if w:v.co=v.co.lerp(pivot+rotation@(v.co-pivot),w)
co=np.array([v.co[:] for v in me.vertices]);foot=co[co[:,2]<.025]
offset=(foot.min(0)+foot.max(0))/2;offset[2]=co[:,2].min()
co-=offset
edges=np.array([e.vertices[:] for e in me.edges]);old=np.linalg.norm(before[edges[:,0]]-before[edges[:,1]],axis=1);new=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)
ratios=new/np.maximum(old,1e-9);assert ratios.max()<1.6,ratios.max()
me.vertices.foreach_set('co',co.ravel());me.update()
me.attributes['orig_co'].data.foreach_set('vector',co.ravel())
# Pack the existing two projection textures into one opaque atlas without changing their RGB pixels.
imgs=[next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE') for mat in me.materials]
w,h=imgs[0].size;assert all(tuple(im.size)==(w,h) for im in imgs)
pixels=np.concatenate([np.array(im.pixels[:]).reshape(h,w,4) for im in imgs],axis=1)
pixels[:,:,3]=1
atlas=bpy.data.images.new('RigProjectionOpaqueAtlas',width=w*2,height=h,alpha=False)
atlas.pixels.foreach_set(pixels.astype('float32').ravel());atlas.pack()
uv=me.uv_layers.active
for f in me.polygons:
 for li in f.loop_indices:uv.data[li].uv.x=(uv.data[li].uv.x+f.material_index)/2
 f.material_index=0
mat=bpy.data.materials.new('RigProjectionOpaque');mat.use_nodes=True;mat.use_backface_culling=True
bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.85;bsdf.inputs['Metallic'].default_value=0
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=atlas
mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);me.materials.clear();me.materials.append(mat)
assert abs(np.ptp(co[:,2])-1.7)<1e-5
for obj in bpy.data.objects:obj.select_set(obj==body)
bpy.context.view_layer.objects.active=body
blend=P/'work/kept_m_clean_v2.blend';glb=blend.with_suffix('.glb')
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_yup=True,export_animations=False,export_skins=False,export_attributes=False,export_materials='EXPORT',export_image_format='AUTO')
report=dict(source='work/kept_m_clean_v1.blend',source_sha256=hashlib.sha256((P/'work/kept_m_clean_v1.blend').read_bytes()).hexdigest(),
 source_upload_sha256=hashlib.sha256((P/'work/kept_m_clean_v1.glb').read_bytes()).hexdigest(),
 blend=str(blend.relative_to(P)),blend_sha256=hashlib.sha256(blend.read_bytes()).hexdigest(),upload=str(glb.relative_to(P)),sha256=hashlib.sha256(glb.read_bytes()).hexdigest(),
 triangles=sum(len(f.vertices)-2 for f in me.polygons),vertices=len(me.vertices),
 changes=['Raised each arm 20 degrees into a wider A-pose with blended shoulder/sleeve transition; no topology change.',
 'Translated sole-bottom bounding centre to the origin; retained 1.7 m height and glTF +Z facing.',
 'Packed existing front/back projection RGB into one opaque material and primitive; no final texture claim.'],
 translation_blender=(-offset).tolist(),max_edge_stretch=float(ratios.max()),min_edge_stretch=float(ratios.min()),reason='HTTP 422 was pose-estimation failure without specific defect. Both v1 axes/scales were valid; v2 improves silhouette and simplifies material handling. Service acceptance is unverified.')
(P/'review/geometry/m_retry_v2.json').write_text(json.dumps(report,indent=2)+'\n')
(P/'requests/kept_m_joints_v2.json').write_text(json.dumps({'model_url':'@file:work/kept_m_clean_v2.glb','height_meters':1.7},indent=2)+'\n')
print(json.dumps(report),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
