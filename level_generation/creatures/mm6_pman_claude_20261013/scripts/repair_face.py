"""Remove overlapping eye/mouth inserts and locally relax noisy face features before UVs."""
from pathlib import Path
import bpy,bmesh,sys,json,runpy
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduced_v1.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
me=body.data;bm=bmesh.new();bm.from_mesh(me);pl=bm.verts.layers.int['piece']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pl] in (8,9,12)],context='VERTS')
# Two small accidental face holes (one beside the nostril, one beside the ear); leave the neck opening intact.
bedges=[e for e in bm.edges if e.is_boundary and all(v[pl]==1 and v.co.z>1.49 for v in e.verts)]
filled=bmesh.ops.holes_fill(bm,edges=bedges,sides=4)['faces']
bmesh.ops.triangulate(bm,faces=filled)
regions=[((-0.028,-0.073,1.569),(.022,.040,.019),.85),((.016,-.073,1.569),(.022,.040,.019),.85),((-.006,-.085,1.521),(.032,.04,.013),.8),((-.006,-.093,1.542),(.023,.025,.010),.45)]
weights={}
for v in bm.verts:
 if v[pl]!=1 or v.co.y>-.025:continue
 w=max(strength*max(0,1-Vector(((v.co[i]-c[i])/radius[i] for i in range(3))).length) for c,radius,strength in regions)
 if w>0:weights[v]=w
before={v:v.co.copy() for v in weights}
for _ in range(8):
 changes={v:v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges),.5*w) for v,w in weights.items()}
 for v,co in changes.items():v.co=co
maxmove=max((v.co-before[v]).length for v in weights)
bm.to_mesh(me);bm.free();me.update()
# holes_fill duplicated one already filled triangle: remove it before freezing/uploading the mesh.
me.validate(verbose=True)
for f in me.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/reduced_face_v1.blend'))
(P/'work/face_repair.json').write_text(json.dumps({'removed_pieces':[8,9,12],'filled_small_holes':len(filled),'smoothed_vertices':len(weights),'max_displacement_m':maxmove,'triangles':len(me.polygons)},indent=2))
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];bpy.context.scene.frame_set(0)
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/face_repaired'),1.56,.38,views=('front','left','three_quarter'),resolution=(650,650))
runpy.run_path(str(P/'scripts/export_uploads.py'),run_name='__main__')
