"""One shared padded UV layout; preserve the local rig while exporting a static neutral upload."""
import json,sys,os
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from geometry import select,render,triangles
bpy.ops.wm.open_mainfile(filepath=str(P/'work/bulwark_rig.blend'))
rig=bpy.data.objects['BulwarkRig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
parts=[o for o in bpy.context.scene.objects if o.type=='MESH'];select(parts)
neutral=bpy.data.materials.new('Bulwark_Neutral');neutral.use_nodes=True;neutral.use_backface_culling=True
node=neutral.node_tree.nodes['Principled BSDF'];node.inputs['Base Color'].default_value=(.5,.5,.5,1);node.inputs['Roughness'].default_value=.7
for o in parts:
    assert not o.data.validate(verbose=True,clean_customdata=False)
    o.data.materials.clear();o.data.materials.append(neutral)
    for f in o.data.polygons:f.material_index=0
    if not o.data.uv_layers:o.data.uv_layers.new(name='UVMap')
select(parts);bpy.ops.object.join();body=bpy.context.view_layer.objects.active;body.name=body.data.name='Bulwark'
xyz=np.array([[body.data.vertices[vi].co[:] for vi in f.vertices] for f in body.data.polygons],dtype=np.float32)
if '--dump' in sys.argv:
    np.save(P/'work/uv_source.npy',xyz);print('UV_SOURCE_READY',xyz.shape,flush=True);os._exit(0)
packed=np.load(P/'work/packed_uv.npz')
assert np.array_equal(xyz,packed['xyz']), 'Packed UVs belong to different geometry'
uv=body.data.uv_layers.active.data
for face,chart in zip(body.data.polygons,packed['uv']):
    for li,coord in zip(face.loop_indices,chart):uv[li].uv=coord
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.seams_from_islands();bpy.ops.object.mode_set(mode='OBJECT')
# Hard normals only cross atlas boundaries, so tangent-space maps remain continuous.
for edge in body.data.edges:edge.use_edge_sharp=edge.use_edge_sharp and edge.use_seam
uv=body.data.uv_layers.active.data
uvtri=np.array([[uv[li].uv[:] for li in f.loop_indices] for f in body.data.polygons])
assert uvtri.shape[1:]==(3,2) and np.isfinite(uvtri).all() and uvtri.min()>=0 and uvtri.max()<=1
area_uv=np.abs(np.cross(uvtri[:,1]-uvtri[:,0],uvtri[:,2]-uvtri[:,0]))/2
xyz=np.array([[body.data.vertices[vi].co[:] for vi in f.vertices] for f in body.data.polygons])
area3d=np.linalg.norm(np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]),axis=1)/2
assert np.all(area3d>1e-10) and np.all(area_uv>1e-12)
density=2048*np.sqrt(area_uv/area3d)
np.savez(P/'work/uv_triangles.npz',uv=uvtri,xyz=xyz)
report={'triangles':triangles(body),'uv_min':float(uvtri.min()),'uv_max':float(uvtri.max()),'uv_area':float(area_uv.sum()),'degenerate_uv_triangles':0,'pack':json.loads((P/'review/geometry/uv_pack.json').read_text()),'texels_per_metre_p10_p50_p90':np.percentile(density,[10,50,90]).tolist(),'texture_size':2048,'static_upload':'work/bulwark_texture_upload.glb','rig_master':'work/bulwark_uv.blend'}
select([body,rig]);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/bulwark_uv.blend'))
# Static duplicate ensures the upload carries no rig, clips, cameras or lights.
upload=bpy.data.objects.new('Bulwark',body.data.copy());bpy.context.scene.collection.objects.link(upload);select([upload])
bpy.ops.export_scene.gltf(filepath=str(P/'work/bulwark_texture_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=False,export_animations=False,export_materials='EXPORT',export_attributes=False)
bpy.data.objects.remove(upload,do_unlink=True)
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
select([body,rig]);bpy.ops.export_scene.gltf(filepath=str(P/'review/bulwark_rig_preview.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(P/'review/geometry/uv_gate.json').write_text(json.dumps(report,indent=2)+'\n')
# Checker is review-only; the saved master and upload keep neutral materials.
img=bpy.data.images.new('UV_Grid',2048,2048);img.generated_type='UV_GRID'
tex=neutral.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;tex.select=True;neutral.node_tree.nodes.active=tex
neutral.node_tree.links.new(tex.outputs['Color'],node.inputs['Base Color'])
render('uv_checker','TEXTURE')
print('UV_READY',json.dumps(report),flush=True)
