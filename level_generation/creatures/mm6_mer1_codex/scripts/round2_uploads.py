import bpy,bmesh,sys,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/rigged.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
body=bpy.data.objects['Body']
# A fitted leather hanger is garment geometry on the pelvis; the retained Club socket animates independently.
bm=bmesh.new();bm.from_mesh(body.data);part=bm.verts.layers.int['piece'];deform=bm.verts.layers.deform.active;gi=body.vertex_groups['B_Pelvis'].index
rows=[]
for z in [.895,.922]:
 row=[]
 for j in range(12):
  a=2*math.pi*j/12;v=bm.verts.new((-.248+.019*math.cos(a),.105+.019*math.sin(a),z));v[part]=12;v[deform][gi]=1;row.append(v)
 rows.append(row)
for j in range(12):
 f=bm.faces.new((rows[0][j],rows[0][(j+1)%12],rows[1][(j+1)%12],rows[1][j]));f.material_index=12
# Short folded strap reaches into the belt surface.
verts=[]
for p in [(-.239,.088,.905),(-.239,.122,.905),(-.213,.115,.93),(-.213,.085,.93)]:
 v=bm.verts.new(p);v[part]=12;v[deform][gi]=1;verts.append(v)
f=bm.faces.new(verts);f.material_index=12
bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3]);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/with_loop.blend'))
s=(P/'scripts/export_uploads.py').read_text().replace("'work', 'with_club.blend'","'work', 'round2', 'with_loop.blend'").replace("'work', 'texture_upload_master.blend'","'work', 'round2', 'texture_upload_master.blend'").replace("'texturing', 'mer1_body_upload.glb'","'work', 'round2', 'body_texture_upload.glb'").replace("'texturing', 'mer1_head_upload.glb'","'work', 'round2', 'head_texture_upload.glb'")
exec(compile(s,str(P/'scripts/export_uploads.py'),'exec'),{'__name__':'__main__','__file__':str(P/'scripts/export_uploads.py')})
