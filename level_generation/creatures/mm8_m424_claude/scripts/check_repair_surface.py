from pathlib import Path
import bpy,bmesh
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/anatomy_v2_parts.blend'))
for n in ['P03','P04']:
 o=bpy.data.objects[n];bm=bmesh.new();bm.from_mesh(o.data)
 print('SURFACE',n,len(bm.verts),len(bm.faces),'boundary',sum(e.is_boundary for e in bm.edges),'nonmanifold',sum(not e.is_manifold for e in bm.edges),'attrs',[(a.name,a.data_type,a.domain) for a in o.data.attributes],'custom',o.data.has_custom_normals)
 bm.free()
