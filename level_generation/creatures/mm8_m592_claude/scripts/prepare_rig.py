"""Align the inspected mesh and give Meshy a provisional textured rigging input."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,math,sys
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_ogr_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
parts={o.name:o for o in bpy.data.objects if o.type=='MESH'}
assert set(('P00','P01','P02')).issubset(parts)
eye=[sum((v.co for v in parts[n].data.vertices),Vector())/len(parts[n].data.vertices) for n in ('P01','P02')]
line=eye[0]-eye[1];yaw=math.atan2(line.y,line.x);R=Matrix.Rotation(-yaw,3,'Z')
for o in parts.values():
 for v in o.data.vertices:v.co=R@v.co
co=np.array([tuple(v.co) for o in parts.values() for v in o.data.vertices]);shift=(co[:,0].min()+co[:,0].max())/2
for name,o in parts.items():
 for v in o.data.vertices:v.co.x-=shift
 o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(name[1:])]*len(o.data.vertices))
 o.select_set(True)
bpy.context.view_layer.objects.active=parts['P00'];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body'
body.data.materials.clear();co=np.array([tuple(v.co) for v in body.data.vertices]);body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
uv=body.data.uv_layers.active or body.data.uv_layers.new(name='Provisional')
lo=co.min(0);span=co.max(0)-lo
for loop in body.data.loops:
 v=body.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=((v.x-lo[0])/span[0],(v.z-lo[2])/span[2])
mat=bpy.data.materials.new('GuardianProvisional');mat.use_nodes=True;mat.diffuse_color=(.42,.43,.45,1)
tex=bpy.data.images.new('GuardianProvisional',width=16,height=16);tex.generated_color=(.42,.43,.45,1);tex.pack()
node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=tex;mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);body.data.materials.append(mat)
bm=bmesh.new();bm.from_mesh(body.data);remaining={e for e in bm.edges if e.is_boundary};loops=[]
while remaining:
 stack=[remaining.pop()];edges=set(stack)
 while stack:
  e=stack.pop()
  for v in e.verts:
   for nxt in v.link_edges:
    if nxt in remaining:remaining.remove(nxt);edges.add(nxt);stack.append(nxt)
 vs={v for e in edges for v in e.verts};c=sum((v.co for v in vs),Vector())/len(vs)
 loops.append({'edges':len(edges),'perimeter':sum(e.calc_length() for e in edges),'centre':list(c)})
bm.free()
body.data.calc_loop_triangles();assert len(body.data.loop_triangles)>14000
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),use_selection=True,export_animations=False,export_format='GLB',export_extras=False)
report={'yaw_correction_degrees':-math.degrees(yaw),'triangles':len(body.data.loop_triangles),'vertices':len(co),'boundary_components':loops,'input':'meshy/body_smart/model_urls_glb.glb','geometry_changes':'Rigid orientation/centering only; retain three claws, feet, eyes and mane geometry. Provisional planar UV/flat map only for joint estimation. Final Meshy UVs will replace it after rig gates.'}
(P/'review/geometry/preparation.json').write_text(json.dumps(report,indent=2)+'\n');print('PREP',json.dumps({k:v for k,v in report.items() if k!='boundary_components'}),flush=True)
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/geometry/prepared'),.85,2.5,views=('front','left','back','three_quarter'),resolution=(900,900),target=(.15,0))
common.render_views(str(P/'review/geometry/head'),1.28,.68,views=('front','left','three_quarter'),resolution=(600,600),target=(.17,-.4))
print('BOUNDARIES',loops,flush=True)
