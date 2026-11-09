import bpy,sys,os,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
for o in meshes:
 o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(o.name[1:])]*len(o.data.vertices));o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['P00'];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body';body.data.materials.clear()
co=np.array([tuple(v.co) for v in body.data.vertices]);body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
assert co[:,2].min()>-1e-5 and abs(co[:,2].max()-1.7)<1e-4
mat=bpy.data.materials.new('ProvisionalRigTexture');mat.use_nodes=True;im=bpy.data.images.new('RigGray',16,16);im.generated_color=(.6,.6,.6,1);im.pack();tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.links.new(tex.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);body.data.materials.append(mat)
for poly in body.data.polygons:poly.material_index=0
if not body.data.uv_layers:
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/rig_upload.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/clean_body'),.85,1.95,views=('front','left','three_quarter','back'),resolution=(500,700));common.render_views(str(P/'review/clean_head'),1.58,.34,views=('front','left'),resolution=(600,600));common.render_views(str(P/'review/clean_hand'),.82,.3,views=('front','back'),target=(-.44,-.1),resolution=(600,600))
print('GEOMETRY',len(body.data.vertices),sum(len(p.vertices)-2 for p in body.data.polygons),'triangles',flush=True)
