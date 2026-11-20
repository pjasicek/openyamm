import bpy,bmesh,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));body=bpy.data.objects['Jackalman'];body.name='Body';rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bm=bmesh.new();bm.from_mesh(body.data);piece=bm.verts.layers.int['piece'];edges=[e for e in bm.edges if all(v[piece]==1 for v in e.verts) and e.calc_length()>.055 and any(.80<v.co.z<1.07 for v in e.verts)];print('SUBDIVIDE',len(edges),flush=True);bmesh.ops.subdivide_edges(bm,edges=edges,cuts=2,use_grid_fill=True);bm.to_mesh(body.data);bm.free()
from skirt_weights import repair_skirt
repair_skirt(body)
print('TRIANGLES',sum(len(f.vertices)-2 for f in body.data.polygons),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/skirt_candidate.blend'));sys.argv=['gate','--',str(P/'work/skirt_candidate.blend'),'Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget'];runpy.run_path(str(P/'scripts/g6_skirt_poke.py'),run_name='__main__')
