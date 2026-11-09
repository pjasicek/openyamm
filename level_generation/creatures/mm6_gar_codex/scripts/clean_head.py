import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/head_geometry_v1.blend'))
mesh=bpy.data.objects['GargoyleHead']; bm=bmesh.new(); bm.from_mesh(mesh.data)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
boundary=[e for e in bm.edges if e.is_boundary]; bad=[e for e in bm.edges if len(e.link_faces)>2]
seen=set(); loops=[]; filled=0
for e in boundary:
    if e in seen: continue
    stack=[e]; seen.add(e); comp=[]
    while stack:
        a=stack.pop(); comp.append(a)
        for v in a.verts:
            for b in v.link_edges:
                if b.is_boundary and b not in seen: seen.add(b); stack.append(b)
    verts={v for e in comp for v in e.verts}; points=np.array([v.co[:] for v in verts]); extent=float(np.ptp(points,axis=0).max())
    loops.append({'edges':len(comp),'extent':extent,'centre':points.mean(0).tolist()})
    if extent<.025 and len(comp)<=12:
        bmesh.ops.holes_fill(bm,edges=comp,sides=0); filled+=1
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]); bm.to_mesh(mesh.data); bm.free()
for p in mesh.data.polygons: p.use_smooth=True
if mesh.data.has_custom_normals: mesh.data.normals_split_custom_set([(0,0,0)]*len(mesh.data.loops))
(P/'work/head_topology.json').write_text(json.dumps({'boundary_edges':len(boundary),'nonmanifold_edges':len(bad),'boundary_loops':loops,'tiny_loops_filled':filled},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/head_geometry_v2.blend'))
scene=bpy.context.scene; scene.world=bpy.data.worlds.new('HeadReview'); common.workbench_clay(scene)
common.render_views(str(P/'review/head_geometry_v2'),.5,1.2,views=('front','left','three_quarter'),resolution=(900,900))
print('HEAD_TOPOLOGY',len(boundary),len(bad),'filled',filled,'loops',loops[:20])
