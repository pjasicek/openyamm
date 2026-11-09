"""Validate corrected rest surfaces and freeze a filtered static texture revision."""
from pathlib import Path
import bpy,json,numpy as np,hashlib
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_uv_master.blend'));scene=bpy.context.scene
roles=('body','wing','wing_strut','horn');uv_dump={};counts={}
for o in scene.objects:
 if o.type!='MESH' or o.get('material_role') not in roles:continue
 m=o.data;assert not m.validate(verbose=True,clean_customdata=False)
 assert all(np.isfinite(v.co).all() for v in m.vertices)
 assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in m.vertices)
 assert all(sum(g.weight>1e-7 for g in v.groups)<=8 for v in m.vertices)
 uv=m.uv_layers.active.data;coords=np.array([[tuple(uv[i].uv) for i in f.loop_indices] for f in m.polygons]);a,b=coords[:,1]-coords[:,0],coords[:,2]-coords[:,0]
 assert min(abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])/2)>1e-11,(o.name,'degenerate UV')
 uv_dump[o.name]=coords[[f.index for f in m.polygons if f.material_index==0]];counts[o.name]=len(m.polygons)
np.savez_compressed(P/'work/final_uv_triangles.npz',**uv_dump)
for o in scene.objects:
 for owner in (o,o.data.shape_keys if o.type=='MESH' else None):
  if owner and owner.animation_data:
   owner.animation_data.action=None
   for t in owner.animation_data.nla_tracks:t.mute=t.name!='Flight'
scene.frame_set(6);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();clones=[]
for o in list(scene.objects):
 if o.get('material_role') not in roles:continue
 data=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
 c=bpy.data.objects.new('Upload_V2_'+o.name,data);scene.collection.objects.link(c);c.matrix_world=o.matrix_world.copy();clones.append(c)
for o in scene.objects:o.select_set(o in clones)
bpy.context.view_layer.objects.active=clones[0];bpy.ops.object.join();upload=bpy.context.object
mat=bpy.data.materials.new('Neutral_V2');mat.use_nodes=True;upload.data.materials.clear();upload.data.materials.append(mat)
for f in upload.data.polygons:f.material_index=0
path=P/'work/texturing_upload_v2.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_skins=False,export_normals=True,export_texcoords=True)
(P/'work/upload_manifest_v2.json').write_text(json.dumps({'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'pose':'Flight B / 0.125 s','living_triangles':sum(counts.values()),'parts':counts,'reason':'Clean chest from original topology, no flattened/folded patch; all finalized wing UVs retained.'},indent=2)+'\n')
for variant in 'abc':
 request={'model_url':'@file:work/texturing_upload_v2.glb','ai_model':'meshy-7','enable_original_uv':True,'enable_pbr':True,'texture_resolution':'4k','target_formats':['glb'],'multiview_image_urls':['@file:references/'+variant+'/'+view+'.png' for view in ('front','left','back')]}
 (P/'requests'/('texture_'+variant+'_v2.json')).write_text(json.dumps(request,indent=2)+'\n')
print('Frozen corrected texture upload:',sum(counts.values()),'living triangles.',flush=True)
