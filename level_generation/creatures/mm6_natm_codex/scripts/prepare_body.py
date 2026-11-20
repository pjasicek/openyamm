import bpy,bmesh,sys,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
skin=bpy.data.objects['P00'];bm=bmesh.new();bm.from_mesh(skin.data)
edges=[e for e in bm.edges if e.is_boundary];print('SKIN boundary',[(list(e.verts[0].co),list(e.verts[1].co)) for e in edges],flush=True)
# Close two exposed chest tears; eye rims retain their separately modelled eyes.
chest=[e for e in edges if all(.9<v.co.z<1.46 for v in e.verts)]
if chest:bmesh.ops.holes_fill(bm,edges=chest,sides=20)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(skin.data);bm.free()
parts=[o for o in bpy.data.objects if o.type=='MESH'];mantle=[]
for o in parts:
 co=np.array([tuple(v.co) for v in o.data.vertices]);i=int(o.name[1:])
 if i not in (0,1,2,3,10) and co[:,1].mean()>.04 and co[:,2].max()>1.05 and co[:,2].mean()>.82:
  mantle.append(i)
  for v in o.data.vertices:
   if v.co.z<1.48:v.co.z=1.48+(v.co.z-1.48)*.68
 a=o.data.attributes.new('piece','INT','POINT');a.data.foreach_set('value',[i]*len(o.data.vertices))
 o.select_set(True)
bpy.context.view_layer.objects.active=skin;bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body';body.data.materials.clear()
mat=bpy.data.materials.new('Neutral rig surface');mat.use_nodes=True;body.data.materials.append(mat)
im=bpy.data.images.new('Neutral rig texture',width=4,height=4);im.generated_color=(.45,.45,.45,1);im.pack();tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;mat.node_tree.links.new(tx.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
if not body.data.uv_layers:body.data.uv_layers.new(name='UVMap')
for uv in body.data.uv_layers.active.data:uv.uv=(.5,.5)
orig=body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT');orig.data.foreach_set('vector',[x for v in body.data.vertices for x in v.co])
for o in list(bpy.data.objects):
 if o is not body:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/corrected'),.86,1.95,views=('front','left','back','three_quarter'),resolution=(600,900))
(P/'work/geometry_correction.json').write_text(json.dumps({'chest_boundary_edges_filled':len(chest),'mantle_pieces_shortened':mantle,'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'rationale':'Close exposed chest tears; shorten generated feather mantle to native waist extent.'},indent=2))
assert len(body.data.vertices)>5000
