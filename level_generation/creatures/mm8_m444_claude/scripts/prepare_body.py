"""Repair the observed cuff spike and damaged left boot; retain labelled parts for rig fitting."""
import bpy,bmesh,json,os,sys
import numpy as np
from mathutils import Vector
sys.path.insert(0,os.path.dirname(__file__))
import common
p=common.PROJECT
bpy.ops.wm.open_mainfile(filepath=p+'/work/st_v2_parts.blend')
meshes={o.name:o for o in bpy.data.objects if o.type=='MESH'}
# One three-valence cuff vertex was generated 64 cm below its neighbours.
ob=meshes['P12'];bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table()
bad=[v for v in bm.verts if v.co.z<0.85]
assert len(bad)==1 and len(bad[0].link_edges)==3
v=bad[0];v.co=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges)
assert max(e.calc_length() for e in bm.edges)<0.2
bm.to_mesh(ob.data);bm.free()
# Two trouser vertices carry the same erroneous position as the cuff spike.
ob=meshes['P02'];bm=bmesh.new();bm.from_mesh(ob.data)
bad=[v for v in bm.verts if v.co.z<0.36]
assert len(bad)==2
for v in bad:v.co=sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges)
bm.to_mesh(ob.data);bm.free()
# The right boot is intact; matching boots are symmetric in the native source.
left=meshes['P05'];left.data=meshes['P06'].data.copy()
for v in left.data.vertices:v.co.x=-v.co.x
bm=bmesh.new();bm.from_mesh(left.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(left.data);bm.free()
# Lace eyelets belong in the final texture, not dozens of tiny separate mesh pieces.
removed=[]
for n,o in list(meshes.items()):
 if n not in ('P05','P06') and max(v.co.z for v in o.data.vertices)<0.42:
  removed.append(n);bpy.data.objects.remove(o,do_unlink=True);del meshes[n]
classes={0:'head',1:'tunic',2:'trousers',3:'hand',4:'hand',5:'boot',6:'boot',7:'bandolier',9:'belt',10:'sheath',12:'cuff',14:'cuff'}
colors={'head':(.45,.26,.16,1),'hand':(.55,.33,.22,1),'tunic':(.45,.45,.42,1),'trousers':(.035,.3,.17,1),'cuff':(.035,.3,.17,1),'boot':(.2,.1,.045,1),'leather':(.22,.12,.05,1)}
for o in bpy.data.objects:o.select_set(False)
parts=[]
for n,o in meshes.items():
 idx=int(n[1:]);cls=classes.get(idx,'leather');color=colors.get(cls,colors['leather'])
 o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[idx]*len(o.data.vertices))
 m=bpy.data.materials.new(n+'_'+cls);m.use_nodes=True;m.diffuse_color=color
 img=bpy.data.images.new(n+'_provisional',width=4,height=4,alpha=True);img.pixels[:]=list(color)*16;img.pack()
 tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img
 bs=m.node_tree.nodes.get('Principled BSDF');m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.8
 o.data.materials.clear();o.data.materials.append(m)
 if not o.data.uv_layers:o.data.uv_layers.new(name='UVMap')
 for uv in o.data.uv_layers.active.data:uv.uv=(.5,.5)
 for face in o.data.polygons:face.material_index=0;face.use_smooth=True
 o.select_set(True);parts.append({'piece':idx,'class':cls,'vertices':len(o.data.vertices)})
bpy.context.view_layer.objects.active=meshes['P01'];bpy.ops.object.join()
body=bpy.context.view_layer.objects.active;body.name=body.data.name='Body'
co=np.array([tuple(v.co) for v in body.data.vertices]);body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
assert abs(co[:,2].max()-1.7)<.001 and abs(co[:,2].min())<.001
bpy.ops.wm.save_as_mainfile(filepath=p+'/work/step1.blend')
os.makedirs(p+'/export',exist_ok=True)
bpy.ops.export_scene.gltf(filepath=p+'/export/smuggler_clean_v1.glb',use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False,export_materials='EXPORT')
json.dump({'removed_lace_pieces':removed,'parts':parts,'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'provisional_texture_only':True},open(p+'/work/cleanup.json','w'),indent=2)
scene=bpy.context.scene;common.workbench_clay(scene);scene.display.shading.color_type='MATERIAL'
common.render_views(p+'/review/clean_v1',.85,1.95,views=('front','left','back','three_quarter'),resolution=(600,900))
print('CLEAN',len(body.data.vertices),'vertices',len(removed),'lace pieces removed')
