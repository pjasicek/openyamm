from pathlib import Path
import bpy,bmesh,json
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uv_ready.blend'));body=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(body.data);piece=bm.verts.layers.int['piece'];before=len(bm.faces)
# The hem cut left sub-0.2 mm edges; merge them before transferring the service's UVs.
verts=[v for v in bm.verts if v[piece]==0 and v.co.z<.026];bmesh.ops.remove_doubles(bm,verts=verts,dist=.0002);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);after=len(bm.faces);bm.to_mesh(body.data);bm.free();assert before-after==4,(before,after)
(p/'work/texture_geometry_cleanup.json').write_text(json.dumps({'triangles_before':before,'triangles_after':after,'hem_merge_distance_mm':.2},indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_texture_clean.blend'))
