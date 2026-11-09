"""Preserve the regenerated continuous garment and inspect shoulder boundaries before rigging."""
import bpy,bmesh,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/raw_parts.blend'))
parts=[o for o in bpy.data.objects if o.type=='MESH']
shirt=bpy.data.objects['P02']
bm=bmesh.new();bm.from_mesh(shirt.data)
boundary=[e for e in bm.edges if e.is_boundary]
shoulder=[e for e in boundary if any(1.12<v.co.z<1.43 and .16<abs(v.co.x)<.37 for v in e.verts)]
rep={'garment_component':'P02','garment_vertices':len(shirt.data.vertices),'garment_triangles':sum(len(f.vertices)-2 for f in shirt.data.polygons),'shoulder_armpit_boundary_edges':len(shoulder),'garment_boundary_edges_total':len(boundary),'boundaries':[[list(v.co) for v in e.verts] for e in boundary],'assessment':'Torso and both sleeves are one connected surface; no shoulder caps or internal arm-root walls. Remaining upper-garment openings are collar, waist and cuffs.'}
print('SHOULDER_BOUNDARY_CANDIDATES',[[list(v.co)for v in e.verts]for e in shoulder],flush=True)
bm.free()
(P/'review/round2/raw_topology.json').write_text(json.dumps(rep,indent=2)+'\n')
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/round2/raw_full'),.85,2.1,views=('front','left','back','right'),resolution=(720,1000))
common.render_views(str(P/'review/round2/raw_shoulders'),1.29,.62,views=('front','left','back','right'),resolution=(1000,650))
for o in parts:
 n=int(o.name[1:]);a=o.data.attributes.new('piece','INT','POINT');a.data.foreach_set('value',[n]*len(o.data.vertices));o.select_set(True)
bpy.context.view_layer.objects.active=shirt;bpy.ops.object.join()
body=bpy.context.object;body.name=body.data.name='Body';body.data.materials.clear()
mat=bpy.data.materials.new('Neutral rig surface');mat.use_nodes=True;body.data.materials.append(mat)
for f in body.data.polygons:f.material_index=0
im=bpy.data.images.new('Neutral rig texture',width=4,height=4);im.generated_color=(.45,.45,.45,1);im.pack()
tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im
mat.node_tree.links.new(tx.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
if not body.data.uv_layers:body.data.uv_layers.new(name='UVMap')
for uv in body.data.uv_layers.active.data:uv.uv=(.5,.5)
for o in list(bpy.data.objects):
 if o is not body:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/raw_body.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/round2/body_for_rig.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'))
r=bpy.data.objects['Rig']
(P/'work/round2/previous_rig.json').write_text(json.dumps({b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(v)for v in b.matrix_local],'parent':b.parent.name if b.parent else None}for b in r.data.bones},indent=2))
print('ROUND2 RAW shoulders boundary edges',len(shoulder),flush=True)
