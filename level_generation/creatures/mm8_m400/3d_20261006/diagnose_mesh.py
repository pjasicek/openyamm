import bpy,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'body_v1.blend'))
body=bpy.data.objects['Lizardman_Body']
for distance in (1e-7,1e-6,1e-5,1e-4,.0003):
    bm=bmesh.new();bm.from_mesh(body.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=distance)
    print(json.dumps({'distance':distance,'vertices':len(bm.verts),'boundary':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),'degenerate':sum(f.calc_area()<1e-12 for f in bm.faces)}),flush=True)
    bm.free()
