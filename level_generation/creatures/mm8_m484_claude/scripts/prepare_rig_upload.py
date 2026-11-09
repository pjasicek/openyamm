"""Repair corrupted left flank from sound opposite anatomy; preserve closed skin beneath independent kilt."""
import bpy,bmesh,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
for name in ['P00','P01']:
 o=bpy.data.objects[name];bpy.context.view_layer.objects.active=o
 bm=bmesh.new();bm.from_mesh(o.data)
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,0),plane_no=(1,0,0),clear_outer=True,dist=1e-6)
 bm.to_mesh(o.data);bm.free()
 mod=o.modifiers.new('Restore bilateral skin','MIRROR');mod.use_clip=True;mod.use_mirror_merge=True;mod.merge_threshold=.00001;bpy.ops.object.modifier_apply(modifier=mod.name)
for i in [76,78,93,97]:bpy.data.objects.remove(bpy.data.objects[f'P{i:02d}'],do_unlink=True)
body=bpy.data.objects['P00'];bm=bmesh.new();bm.from_mesh(body.data)
# Split only the torso: the hands also reach below the belt.
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,.905),plane_no=(0,0,1),dist=1e-6)
for f in bm.faces:f.select=all(abs(v.co.x)<.4 and v.co.z<=.905001 for v in f.verts)
bm.to_mesh(body.data);bm.free()
for o in bpy.data.objects:o.select_set(o is body)
bpy.context.view_layer.objects.active=body;bpy.ops.object.mode_set(mode='EDIT');bpy.context.tool_settings.mesh_select_mode=(False,False,True);bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
cloth=next(o for o in bpy.context.selected_objects if o is not body);cloth.name='P100'
# The pelvis is present, but Meshy left its waist uncapped; cap both overlapping skin shells.
counts={}
for name in ['P00','P01']:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
 edges=[e for e in bm.edges if e.is_boundary];filled=bmesh.ops.holes_fill(bm,edges=edges,sides=0)['faces'];bmesh.ops.triangulate(bm,faces=filled);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 counts[name]={'filled_faces':len(filled),'remaining_boundary':sum(e.is_boundary for e in bm.edges)}
 assert counts[name]['remaining_boundary']==0,(name,counts[name])
 bm.to_mesh(o.data);bm.free()
parts=[o for o in bpy.data.objects if o.type=='MESH']
for o in bpy.data.objects:o.select_set(o in parts)
for o in parts:
 i=int(o.name[1:]);a=o.data.attributes.new('piece','INT','POINT');a.data.foreach_set('value',[i]*len(o.data.vertices))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body';body.data.materials.clear()
mat=bpy.data.materials.new('Neutral rig surface');mat.use_nodes=True;body.data.materials.append(mat)
im=bpy.data.images.new('Neutral rig texture',width=4,height=4);im.generated_color=(.45,.45,.45,1);im.pack();tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;mat.node_tree.links.new(tx.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
if not body.data.uv_layers:body.data.uv_layers.new(name='UVMap')
for uv in body.data.uv_layers.active.data:uv.uv=(.5,.5)
orig=body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT');orig.data.foreach_set('vector',[x for v in body.data.vertices for x in v.co])
for o in list(bpy.data.objects):
 if o is not body:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
assert len(body.data.vertices)>5000
report={'height_m':1.9,'repairs':['Mirrored sound negative-X skin half to replace collapsed left flank/pelvis and finger boundary','Removed four detached flank artifact pieces 76,78,93,97','Separated kilt below z .905 as piece100','Closed overlapping torso and pelvis skin waist openings'], 'skin_closure':counts,'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'uv':'Provisional constant UV only for rig service'}
(P/'review/geometry_review.json').write_text(json.dumps(report,indent=2));print('GEOMETRY',report)
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/cleaned'),.95,2.15,views=('front','three_quarter','left','back'),resolution=(800,1000))
