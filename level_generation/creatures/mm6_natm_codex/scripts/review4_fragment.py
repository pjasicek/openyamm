import bpy,bmesh,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
rows=[]
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));ob=bpy.data.objects['Body'];before=C.triangles(ob);bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.verts.layers.int['piece'];verts=[v for v in bm.verts if v[layer]==13];count=len(verts);bmesh.ops.delete(bm,geom=verts,context='VERTS');bm.to_mesh(ob.data);bm.free();ob.data.update();rows.append({'lod':level,'removed_vertices':count,'triangles_before':before,'triangles_after':C.triangles(ob),'skin_geometry_removed':False});C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
(P/'review/round4_fragment.json').write_text(json.dumps(rows,indent=2));print('REMOVED_FLOATING_FRAGMENT',rows,flush=True)
