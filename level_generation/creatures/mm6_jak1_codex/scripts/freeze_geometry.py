import bpy,bmesh,json,numpy as np,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
# Close the sole exposed five-edge chest hole; neck/garment openings stay intentional.
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();edges=[e for e in bm.edges if e.is_boundary and all(me.attributes["piece"].data[v.index].value==0 and 1.34<v.co.z<1.41 and .07<v.co.x<.13 for v in e.verts)];assert len(edges)==5,len(edges);filled=bmesh.ops.holes_fill(bm,edges=edges,sides=0)['faces'];bmesh.ops.triangulate(bm,faces=filled);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_full.blend'))
before=len(me.polygons);keep=body.vertex_groups.new(name='DensityKeep');protected=[]
for v in me.vertices:
 co=v.co;protect=co.z>1.44 or abs(co.x)>.46
 for sd in 'LR':
  el=rig.data.bones[f'B_{sd}_Forearm'].head_local
  protect|=(co-el).length<.085
 if protect:protected.append(v.index)
keep.add(protected,1,'REPLACE');fixed=np.array([tuple(me.vertices[i].co)for i in protected]);bpy.context.view_layer.objects.active=body
mod=body.modifiers.new('Final density','DECIMATE');mod.ratio=.66;mod.vertex_group=keep.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name);body.vertex_groups.remove(body.vertex_groups['DensityKeep'])
for v in me.vertices:
 w=sorted([(g.group,g.weight)for g in v.groups if g.weight>1e-7],key=lambda x:-x[1])[:4];total=sum(x for _,x in w);assert total>0
 for g in v.groups[:]:body.vertex_groups[g.group].remove([v.index])
 for g,x in w:body.vertex_groups[g].add([v.index],x/total,'REPLACE')
me.attributes.new('head','INT','FACE');me.calc_loop_triangles();report={'before_triangles':before,'after_triangles':len(me.loop_triangles),'protected_vertices_before':len(fixed),'filled_chest_hole_faces':len(filled),'influence_limit':4};print('REDUCTION',report,flush=True);(P/'work/reduction.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_body.blend'))
# Rest-only whole body, no staff, rig, or animation enters the paid texture job.
ob=bpy.data.objects.new('JackalmanUpload',me.copy());bpy.context.collection.objects.link(ob)
for o in bpy.data.objects:o.select_set(o==ob)
bpy.context.view_layer.objects.active=ob;bpy.ops.export_scene.gltf(filepath=str(P/'work/body_retexture.glb'),use_selection=True,export_format='GLB',export_skins=False,export_animations=False,export_attributes=False)
roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
for n,extra in [('g4_weights.py',['reduced']+[f'{r}:{f}'for r in roles for f in range(0,int(bpy.data.actions[r].frame_range[1])+1,2)]),('g5_hand_stretch.py',roles),('g6_contacts.py',roles),('g6_skirt_poke.py',roles)]:
 sys.argv=[n,'--',str(P/'work/production_body.blend'),*extra];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
