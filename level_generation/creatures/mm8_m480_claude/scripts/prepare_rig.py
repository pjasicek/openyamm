"""Repair the two extra posterior digits and small skin holes, retain native cloth/crest shells."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,runpy,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/body_v1_parts.blend'));skin=bpy.data.objects['P00'];co=np.array([tuple(v.co) for v in skin.data.vertices]);adj=[[] for v in co]
for e in skin.data.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
remove=set();rep={}
for sg,cut in [(-1,.634),(1,.632)]:
 tip=int(np.argmin(np.linalg.norm(co-np.array([sg*.53,.035,.535]),axis=1)));valid=(co[:,0]*sg>.39)&(co[:,2]<cut)&(co[:,2]>.4);seen=set();stack=[tip]
 while stack:
  v=stack.pop()
  if v in seen or not valid[v]:continue
  seen.add(v);stack.extend(adj[v])
 assert 80<len(seen)<120 and co[list(seen),1].min()>-.04
 remove|=seen;rep[str(sg)]={'extra_digit_vertices_removed':len(seen),'cut_z':cut}
bm=bmesh.new();bm.from_mesh(skin.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS');bmesh.ops.delete(bm,geom=[e for e in bm.edges if e.is_wire],context='EDGES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_edges],context='VERTS');bounds=[e for e in bm.edges if e.is_boundary]
filled=bmesh.ops.holes_fill(bm,edges=bounds,sides=0)['faces'];bmesh.ops.triangulate(bm,faces=filled)
remaining=[e for e in bm.edges if e.is_boundary]
while remaining:
 loop=[remaining[0].verts[0]];start=loop[0];cur=remaining[0].verts[1]
 while cur is not start:
  loop.append(cur);nxt=[e.other_vert(cur) for e in cur.link_edges if e.is_boundary and e.other_vert(cur) is not loop[-2]];assert len(nxt)==1;cur=nxt[0]
 assert len(loop)<=8
 center=bm.verts.new(sum((v.co for v in loop),loop[0].co*0)/len(loop))
 for i,v in enumerate(loop):bm.faces.new((v,loop[(i+1)%len(loop)],center))
 remaining=[e for e in bm.edges if e.is_boundary]
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges),[(len(e.link_faces),[list(v.co) for v in e.verts]) for e in bm.edges if not e.is_manifold];bm.to_mesh(skin.data);bm.free()
# Six isolated single triangles inside the crest are generation debris, not silhouette components.
removed=[]
for o in list(bpy.data.objects):
 if o.type=='MESH' and len(o.data.polygons)==1:
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
parts=[o for o in bpy.data.objects if o.type=='MESH']
for o in bpy.data.objects:o.select_set(False)
for o in parts:
 o.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(o.name[1:])]*len(o.data.vertices));o.select_set(True)
bpy.context.view_layer.objects.active=skin;bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body';body.data.materials.clear()
co=np.array([tuple(v.co) for v in body.data.vertices]);body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15192,island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
mat=bpy.data.materials.new('TrollProvisional');mat.use_nodes=True;tex=bpy.data.images.new('TrollProvisional',width=16,height=16);tex.generated_color=(.32,.25,.15,1);tex.pack();node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=tex;mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);body.data.materials.append(mat)
for p in body.data.polygons:p.use_smooth=True
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/body_v2'),.85,2.2,views=('front','left','back','three_quarter'),resolution=(600,900));common.render_views(str(P/'review/body_v2_hand'),.59,.43,views=('front','left'),resolution=(700,700),target=(.52,-.04))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'));bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),use_selection=True,export_animations=False,export_format='GLB',export_extras=False)
(P/'review/geometry_repairs.json').write_text(json.dumps({'digits':rep,'removed_single_triangle_parts':removed,'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'skin_manifold':True,'cloth_open_shells':'retained; thin cloth must retain two-sided rendering'},indent=2)+'\n')
s=P/'scripts/source_rest.py';sys.argv=[str(s),'--',str(P.parents[2]/'anim_library/humanoid_set/Armed.glb')];runpy.run_path(str(s),run_name='__main__')
f=P/'work/source_rest.json';a=json.loads(f.read_text());a={k:v for k,v in a.items() if not k.startswith(('B_L_Finger3','B_R_Finger3'))};f.write_text(json.dumps(a,indent=1));assert len([k for k in a if 'Finger' in k])==24
