"""Replace the orbital bump's folded central topology with a clean concave socket floor."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_complete.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
off=json.loads((P/'work/skull_fit.json').read_text())['offset'];bm=bmesh.new();bm.from_mesh(body.data)
pl=bm.verts.layers.int['piece'];deform=bm.verts.layers.deform.verify();report=[]
for s in [-1,1]:
    cx=off[0]+s*.027;cz=1.675
    def radius(v):return ((v.co.x-cx)**2+(v.co.z-cz)**2)**.5
    cut=[v for v in bm.verts if v[pl]==2000 and v.co.y<0 and radius(v)<.0115]
    bmesh.ops.delete(bm,geom=cut,context='VERTS')
    edges=[e for e in bm.edges if e.is_boundary and all(v[pl]==2000 and v.co.y<.01 and radius(v)<.020 for v in e.verts)]
    assert len(edges)>8,(s,len(edges))
    filled=bmesh.ops.holes_fill(bm,edges=edges,sides=0)['faces'];assert filled
    print('SOCKET LOOPS',s,[(len(f.verts),f.calc_area(),list(f.calc_center_median()))for f in filled])
    made=bmesh.ops.poke(bm,faces=filled,offset=0,center_mode='MEAN_WEIGHTED')
    for v in made['verts']:
        v.co.y+=.004;v[pl]=2000;v[deform].clear();v[deform][body.vertex_groups['B_Head'].index]=1
    for f in made['faces']:f.smooth=True;f.material_index=0
    report.append({'side':s,'removed_vertices':len(cut),'rim_edges':len(edges),'new_triangles':len(made['faces'])})
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
bpy.context.view_layer.update();common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/skull_socket'),1.68,.30,views=('front','three_quarter'),resolution=(600,600),target=(off[0],off[1]))
(P/'work/socket_repair.json').write_text(json.dumps(report,indent=2));print(report)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_complete.blend'))
