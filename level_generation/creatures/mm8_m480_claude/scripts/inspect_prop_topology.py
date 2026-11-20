from pathlib import Path
import bpy,bmesh,json
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/club.blend'));o=bpy.data.objects['Club'];bm=bmesh.new();bm.from_mesh(o.data)
print('PROP TOPOLOGY',len(bm.verts),len(bm.faces),'boundary',sum(e.is_boundary for e in bm.edges),'nonmanifold',sum(not e.is_manifold and not e.is_boundary for e in bm.edges),'volume',bm.calc_volume(signed=True),flush=True)
