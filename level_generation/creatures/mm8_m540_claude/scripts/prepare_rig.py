"""Prepare the Mage body for joint estimation; preserve all five fingers and layered costume."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,sys,runpy
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
assert len(parts)==28
cloth=parts['P01'];moved=0
for v in cloth.data.vertices:
 if v.co.y>.10 and v.co.z<.85:
  v.co.z+=.18*min(1,(.85-v.co.z)/.79);moved+=1
# Close small accidental garment perforations; retain the large neck, arm and hem openings.
bm=bmesh.new();bm.from_mesh(cloth.data)
boundary={e for e in bm.edges if e.is_boundary};loops=[]
while boundary:
 stack=[boundary.pop()];es=set(stack)
 while stack:
  e=stack.pop()
  for v in e.verts:
   for nxt in v.link_edges:
    if nxt in boundary:boundary.remove(nxt);es.add(nxt);stack.append(nxt)
 loops.append(es)
closed=[]
for es in loops:
 per=sum(e.calc_length() for e in es)
 if len(es)<=12 and per<.11:
  res=bmesh.ops.holes_fill(bm,edges=list(es),sides=0);closed.append({'edges':len(es),'perimeter':per,'faces':len(res['faces'])})
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cloth.data);bm.free()
# A thin clearance margin on the shoulder cape prevents the underlying skin breaking through its cloth.
for v in cloth.data.vertices:
 if 1.08<v.co.z<1.40 and v.co.y>.04:
  v.co+=v.normal*.006
for o in bpy.data.objects:o.select_set(False)
for name,o in parts.items():
 o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(name[1:])]*len(o.data.vertices));o.select_set(True)
bpy.context.view_layer.objects.active=parts['P00'];bpy.ops.object.join()
body=bpy.context.object;body.name=body.data.name='Body';body.data.materials.clear()
co=np.array([tuple(v.co) for v in body.data.vertices])
body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15192,island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
mat=bpy.data.materials.new('MageProvisional');mat.use_nodes=True
tex=bpy.data.images.new('MageProvisional',width=16,height=16);tex.generated_color=(.35,.29,.24,1);tex.pack()
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=tex
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
assert len(body.data.uv_layers)==1 and moved>20
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(p/'work/body_for_rig.glb'),use_selection=True,export_animations=False,export_format='GLB',export_extras=False)
report={'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'cape_vertices_shortened':moved,'small_holes_closed':closed,'head':'separate correction in progress; this upload estimates body joints only'}
(p/'review/geometry/preparation.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/geometry/prepared'),.85,2.5,views=('front','left','back','three_quarter'),resolution=(600,900))
s=p/'scripts/source_rest.py';sys.argv=[str(s),'--',str(p.parents[2]/'anim_library/humanoid_set/Armed.glb')];runpy.run_path(str(s),run_name='__main__')
assert len([n for n in json.loads((p/'work/source_rest.json').read_text()) if 'Finger' in n])==30
