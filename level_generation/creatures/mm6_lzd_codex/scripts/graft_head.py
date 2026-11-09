"""Replace the disconnected pointed head with the reviewed, broad-snout bust before autorigging."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
body=bpy.data.objects['Body'];parts=json.loads((P/'work/st_v1_parts.json').read_text())
remove={int(x['name'][1:]) for x in parts if x['mean'][2]>1.48 and x['mean'][1]<-.28};remove.update([0,200])
bm=bmesh.new();bm.from_mesh(body.data);pa=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pa] in remove],context='VERTS');bm.to_mesh(body.data);bm.free()
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy/head_geometry_v1/model_urls_glb.glb'))
heads=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in heads:o.select_set(True)
bpy.context.view_layer.objects.active=heads[0];bpy.ops.object.join();head=bpy.context.object;head.name='ReplacementHead';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([tuple(v.co)for v in head.data.vertices]);lo=co.min(0);hi=co.max(0);s=.40/(hi[2]-lo[2]);neck=co[co[:,2]<lo[2]+.04*(hi[2]-lo[2])].mean(0)
for v in head.data.vertices:v.co=((v.co.x-neck[0])*s,(v.co.y-neck[1])*s+.015,(v.co.z-lo[2])*s+1.30)
attr=head.data.attributes.new('piece','INT','POINT');attr.data.foreach_set('value',[200]*len(head.data.vertices))
for m in head.data.materials:m.name='LizardHead_A'
bm=bmesh.new();bm.from_mesh(head.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(head.data);bm.free()
head.data.normals_split_custom_set([(0,0,0)]*len(head.data.loops))
for poly in head.data.polygons:poly.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/head_graft_separate.blend'))
body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
orig=body.data.attributes.get('orig_co');orig.data.foreach_set('vector',[x for v in body.data.vertices for x in v.co])
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
rep={'replaced_parts':sorted(remove),'head_vertices':len(co),'head_source_bounds':[lo.tolist(),hi.tolist()],'scale':s,'head_height_m':.40,'neck_floor_m':1.30,'body_triangles':sum(len(f.vertices)-2 for f in body.data.polygons)}
(P/'work/head_graft.json').write_text(json.dumps(rep,indent=2));print('GRAFT',rep)
scene=bpy.context.scene;common.workbench_clay(scene,textured=True)
common.render_views(str(P/'review/head_graft_body'),.85,2.02,views=('front','left','three_quarter'),resolution=(800,900))
common.render_views(str(P/'review/head_graft_close'),1.50,.50,views=('front','left','three_quarter'),resolution=(800,800),target=(0,-.05))
