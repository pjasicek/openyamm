import bpy,bmesh,json,sys,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_render import render
from round3_candidate_gates import check
best=None
for source,tag in [('contour2','qem3a'),('loft2','qem3b')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/rebake/{source}.blend'));me=bpy.data.objects['Body'].data;pv=np.array([v.value for v in me.attributes['piece'].data]);ids=np.where(pv==201)[0];remap={int(old):new for new,old in enumerate(ids)};coords=[tuple(me.vertices[i].co)for i in ids];polys=[f for f in me.polygons if all(pv[i]==201 for i in f.vertices)];faces=[[remap[i]for i in f.vertices]for f in polys];uvs=[[tuple(me.uv_layers.active.data[i].uv)for i in f.loop_indices]for f in polys]
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/rebake/contour3.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 mat=next(m for m in body.data.materials if 'Bow'in m.name);me=bpy.data.meshes.new('ContinuousBow');me.from_pydata(coords,[],faces);me.materials.append(mat);uv=me.uv_layers.new(name='UVMap')
 for f,values in zip(me.polygons,uvs):
  f.use_smooth=True
  for li,v in zip(f.loop_indices,values):uv.data[li].uv=v
 ob=bpy.data.objects.new('ContinuousBow',me);bpy.context.collection.objects.link(ob);ob.vertex_groups.new(name='Bow').add(list(range(len(coords))),1,'REPLACE');me.attributes.new('piece','INT','POINT').data.foreach_set('value',[201]*len(coords));bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 count=sum(len(f.vertices)-2 for f in me.polygons);m=ob.modifiers.new('Continuous surface collapse','DECIMATE');m.ratio=116/count;m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
 bm=bmesh.new();bm.from_mesh(body.data);la=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[la]==201],context='VERTS');bm.to_mesh(body.data);bm.free();body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
 a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();posed=np.array([tuple(v.co)for v in m.vertices]);ev.to_mesh_clear();pv=np.array([v.value for v in body.data.attributes['piece'].data]);ids=np.where(pv==201)[0];remap=np.full(len(pv),-1);remap[ids]=np.arange(len(ids));body.data.calc_loop_triangles();tris=np.array([tuple(f.vertices)for f in body.data.loop_triangles]);faces=remap[tris[np.all(pv[tris]==201,axis=1)]]
 path=P/f'work/rebake/{tag}_bow.npz';np.savez(path,vertices=posed[ids],faces=faces,part='bow',level=3);subprocess.run(['/usr/bin/python3',str(P/'scripts/contour_silhouette_fit.py'),str(path)],check=True);fit=np.load(path.with_suffix('.npy'));inverse=(rig.pose.bones['Bow'].matrix@rig.data.bones['Bow'].matrix_local.inverted()).inverted()
 for i,point in zip(ids,fit):body.data.vertices[i].co=inverse@Vector(point)
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();path=P/f'work/rebake/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));render(path,tag,3,parts=['bow'])
 metrics=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,'3','8','bow'],text=True));(P/f'review/rebake/{tag}_geometry_metrics.json').write_text(json.dumps(metrics,indent=2));print('FAR_BOW',tag,len(faces),metrics['bow']['pooled_iou'],flush=True)
 if best is None or metrics['bow']['pooled_iou']>best[0]:best=(metrics['bow']['pooled_iou'],tag)
 if metrics['bow']['passed']:break
for tag in ['plain1','contour2',best[1]]:
 try:r=check(P/f'work/rebake/{tag}.blend')
 except Exception as e:r={'passed':False,'error':repr(e)}
 (P/f'review/rebake/{tag}_gates.json').write_text(json.dumps(r,indent=2));print('SELECTED_LOD_GATES',tag,{k:v for k,v in r.items()if k!='motion'},r.get('motion',{}).get('issues',[]),flush=True)
