"""Evaluate topology reduction before spending time rebaking a candidate that fails deformation gates."""
import bpy,bmesh,math,json,os,runpy,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];out=p/'review/round3/reduction';out.mkdir(exist_ok=True)
baseline=(p/'work/gates_dense.json').read_bytes();rows=[]
for ratio in [.95,.85,.65]:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'))
 r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();bm=bmesh.new();bm.from_mesh(b.data);pv=bm.verts.layers.int['piece'];protected=set()
 joints=[r.data.bones[f'B_{sd}_{part}'].head_local for sd in 'LR' for part in ['UpperArm','Forearm','Hand','Thigh','Calf']]
 directions=[np.array([math.sin(a),math.cos(a),0.]) for a in np.arange(8)*math.pi/4]
 for v in bm.verts:
  if v[pv] in [2,3] or any((v.co-j).length<.065 for j in joints):protected.add(v.index)
 for e in bm.edges:
  if len(e.link_faces)!=2 or any(np.dot(e.link_faces[0].normal,d)*np.dot(e.link_faces[1].normal,d)<0 for d in directions):
   protected.update(v.index for v in e.verts)
 group=b.vertex_groups.new(name='_reduction_protected');group.add(list(protected),1,'REPLACE')
 # BMesh was read before the protection group existed; write its deform data back explicitly.
 deform=bm.verts.layers.deform.verify()
 for v in bm.verts:
  if v.index in protected:v[deform][group.index]=1
 edges=[e for e in bm.edges if not any(v.index in protected for v in e.verts)]
 bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(3),verts=[],edges=edges,use_dissolve_boundaries=False)
 bm.to_mesh(b.data);bm.free()
 bpy.ops.object.select_all(action='DESELECT');b.select_set(True);bpy.context.view_layer.objects.active=b
 mod=b.modifiers.new('Protected silhouette reduction','DECIMATE');mod.ratio=ratio;mod.vertex_group=group.name;mod.invert_vertex_group=True;mod.vertex_group_factor=1000;mod.use_collapse_triangulate=True
 bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
 b.vertex_groups.remove(b.vertex_groups['_reduction_protected']);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 tris=sum(len(f.vertices)-2 for f in b.data.polygons);name=f'candidate_{ratio:.2f}';dest=p/f'work/{name}.blend'
 bpy.ops.wm.save_as_mainfile(filepath=str(dest));os.environ['GATE_BLEND']=str(dest.relative_to(p));runpy.run_path(str(p/'scripts/gates_dense.py'),run_name='__main__')
 gates=json.loads((p/'work/gates_dense.json').read_text());(out/f'{name}_rig.json').write_text(json.dumps(gates,indent=2))
 row={'candidate':str(dest.relative_to(p)),'ratio':ratio,'triangles':tris,'protected_vertices':len(protected),'G4_max':max(v['stretch'][s+'_arm']['p99'] for v in gates.values() for s in 'LR'),'G5_max':max(v['stretch'][s+'_hand']['max'] for v in gates.values() for s in 'LR'),'rig_pass':all(v['G4_pass'] and v['G5_pass'] for v in gates.values())}
 rows.append(row);print('REDUCTION',row,flush=True)
(p/'work/gates_dense.json').write_bytes(baseline);os.environ.pop('GATE_BLEND',None)
(out/'candidates.json').write_text(json.dumps(rows,indent=2))
