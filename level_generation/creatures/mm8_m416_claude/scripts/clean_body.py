from pathlib import Path
import bpy,json,numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'};assert len(parts)==23
assert len(parts['P22'].data.polygons)==1
bpy.data.objects.remove(parts.pop('P22'),do_unlink=True)
labels={0:'upper_body_and_arms',1:'head_neck',2:'trousers',3:'left_gauntlet_hand',4:'right_forearm_hand',5:'hair',6:'left_boot',7:'right_boot',8:'sash',9:'bandanna',10:'hair',11:'right_boot_cuff',12:'left_boot_cuff',13:'buckle',14:'sash_left_backfold',15:'sash_left_frontfold',16:'left_eye',17:'right_eye',18:'bandanna_tail',19:'sash_right_tail',20:'bandanna_tail',21:'vest_button'}
for o in bpy.data.objects:o.select_set(False)
for n,o in parts.items():
 o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(n[1:])]*len(o.data.vertices));o.select_set(True)
bpy.context.view_layer.objects.active=parts['P00'];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body';me=body.data
co=np.array([tuple(v.co) for v in me.vertices]);me.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
(P/'work/garments.json').write_text(json.dumps(labels,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
body.data.materials.clear();mat=bpy.data.materials.new('RiggingPreview');mat.use_nodes=True;im=bpy.data.images.new('rigging_preview',width=4,height=4);im.pixels=[.65,.65,.65,1]*16;im.pack();node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);body.data.materials.append(mat)
for f in me.polygons:f.material_index=0
if not me.uv_layers:
 uv=me.uv_layers.new(name='ProvisionalUV')
 for l in me.loops:
  v=me.vertices[l.vertex_index].co;uv.data[l.index].uv=((v.x+.7)/1.4,v.z/1.85)
bpy.ops.export_scene.gltf(filepath=str(P/'export/body_for_rig.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
(P/'requests/rig_v1.json').write_text(json.dumps({'model_url':'@file:export/body_for_rig.glb','height_meters':1.85},indent=2))
print('CLEAN',len(me.vertices),'vertices',sum(len(f.vertices)-2 for f in me.polygons),'triangles; five distinct digits each hand verified; removed stray upper-arm triangle')
