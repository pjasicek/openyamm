"""Label native components and stage the reviewed body for joint estimation."""
from pathlib import Path
import bpy,bmesh,json,sys
import numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
labels={0:'coat_shirt',1:'head_neck',2:'hair',3:'left_hand',4:'breeches',5:'right_hand',6:'left_leg_shoe',7:'beard',8:'beard',9:'sash',10:'left_shirt_cuff',11:'right_shirt_cuff',12:'right_peg',13:'left_coat_cuff',14:'right_coat_cuff',15:'right_eye',16:'left_eye',17:'beard',18:'shoe_buckle',19:'beard',20:'beard',21:'beard',22:'beard'}
colors={'cloth':(.025,.13,.045,1),'skin':(.58,.36,.23,1),'hair':(.07,.025,.012,1),'pants':(.23,.23,.22,1),'white':(.72,.69,.60,1),'wood':(.23,.105,.035,1),'red':(.20,.035,.02,1),'gold':(.48,.32,.08,1)}
mats={}
for name,col in colors.items():
 m=bpy.data.materials.new('Mage_'+name);m.use_nodes=True;m.diffuse_color=col
 im=bpy.data.images.new('Provisional_'+name,8,8);im.generated_color=col;im.pack()
 tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;bs=m.node_tree.nodes.get('Principled BSDF');m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.8;mats[name]=m
wrists={}
for o in [o for o in bpy.data.objects if o.type=='MESH']:
 n=int(o.name[1:]);assert n in labels
 kind='skin' if n in [1,3,5] else 'hair' if n in [2,7,8,17,19,20,21,22] else 'pants' if n in [4,6] else 'white' if n in [10,11] else 'wood' if n==12 else 'red' if n==9 else 'gold' if n==18 else 'cloth'
 o.data.materials.clear();o.data.materials.append(mats[kind]);o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[n]*len(o.data.vertices))
 for f in o.data.polygons:f.use_smooth=True
 if n in [3,5]:
  bm=bmesh.new();bm.from_mesh(o.data);vs={v for e in bm.edges if e.is_boundary for v in e.verts};assert len(vs)==15
  wrists['L' if n==3 else 'R']=np.mean([v.co[:] for v in vs],axis=0).tolist();bm.free()
 if not o.data.uv_layers:
  uv=o.data.uv_layers.new(name='ProvisionalUV')
  for loop in o.data.loops:
   c=o.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=((c.x+.7)/1.4,c.z/1.7)
for o in bpy.data.objects:o.select_set(o.type=='MESH')
bpy.context.view_layer.objects.active=bpy.data.objects['P00'];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body'
assert not body.data.validate();body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',[x for v in body.data.vertices for x in v.co])
(p/'work/parts_labels.json').write_text(json.dumps(labels,indent=2));(p/'work/wrists.json').write_text(json.dumps(wrists,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_format='GLB',export_animations=False,export_skins=False,export_attributes=False)
(p/'requests/rig_v1.json').write_text(json.dumps({'model_url':'@file:work/body_for_rig.glb','height_meters':1.7},indent=2))
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/clean'),.85,1.95,views=('front','left','back','three_quarter'),resolution=(600,900))
print('PARTS',len(labels),'triangles',sum(len(f.vertices)-2 for f in body.data.polygons),'WRISTS',wrists)
