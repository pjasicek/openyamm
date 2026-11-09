import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
rig.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(p/'work/robe_v5.blend'),link=False) as (a,b):b.actions=[n for n in a.actions if n in ['Standing','Walking','Attack','Cast','Hit','Death','Fidget']]
for a in b.actions:a.use_fake_user=True
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update()
pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices]);ids=np.where(pv==100)[0];angle=np.arctan2(co[:,0],co[:,1]+.02);radius=np.hypot(co[:,0],co[:,1]+.02)
# The original combined shoe/robe surface was hit by radial samples below the true hem. Correct those rows
# from the intact robe ring at 27 cm, preserving its fold phase and UVs.
anchor=ids[(co[ids,2]>.25)&(co[ids,2]<.30)];assert len(anchor)>20
A=np.linspace(-math.pi,math.pi,65);R=[]
for a in A:
 da=np.abs((angle[anchor]-a+math.pi)%(2*math.pi)-math.pi);near=anchor[np.argsort(da)[:5]];R.append(float(np.median(radius[near])))
med=float(np.median(R));changed=0
for i in ids:
 if co[i,2]>=.27:continue
 t=float(np.clip((.27-co[i,2])/(.27-.125),0,1));ra=float(np.interp(angle[i],A,R));rhem=max(.29,med+.015)+.6*(ra-med)
 want=radius[i]*(1-t)+rhem*t
 me.vertices[int(i)].co.x=math.sin(angle[i])*want;me.vertices[int(i)].co.y=-.02+math.cos(angle[i])*want;changed+=1
# A second singular anchor at the nose joined unrelated forehead/cheek/lip triangles. Remove it and fill
# the genuine local skin holes, leaving the neck opening and separate eyeballs intact.
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();pl=bm.verts.layers.int['piece'];hl=bm.faces.layers.int['head']
bad=[v for v in bm.verts if v[pl]==2 and (v.co-__import__('mathutils').Vector((.0016068404,-.0829342678,1.5828232765))).length<.0001]
assert 1<=len(bad)<=40,len(bad)
bmesh.ops.delete(bm,geom=bad+[v for v in bm.verts if v[pl] in [13,14,15]],context='VERTS')
bmesh.ops.remove_doubles(bm,verts=[v for v in bm.verts if v[pl]==2],dist=.000001)
boundary=[e for e in bm.edges if e.is_boundary and all(v[pl]==2 and v.co.z>1.47 for v in e.verts)]
filled=0
for attempt in range(5):
 boundary=[e for e in bm.edges if e.is_boundary and all(v[pl]==2 and v.co.z>1.47 for v in e.verts)]
 if not boundary:break
 new=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)['faces'];filled+=len(new)
 for face in new:face[hl]=1;face.smooth=True
 bmesh.ops.triangulate(bm,faces=list(new))
 print('FILL',attempt,len(boundary),len(new),flush=True)
 if not new:break
for _ in range(3):
 bmesh.ops.smooth_vert(bm,verts=[v for v in bm.verts if v[pl]==2 and v.co.z>1.61 and v.co.y<-.035],factor=.4,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
remaining=[e for e in bm.edges if e.is_boundary and all(v[pl]==2 and v.co.z>1.47 for v in e.verts)]
print('REPAIRS hem vertices',changed,'head faces filled',filled,'head boundaries left',len(remaining))
assert all(max(v.co.z for v in e.verts)<1.61 for e in remaining), 'unclosed forehead defect'
bm.to_mesh(me);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_surface_repaired.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/surface_repair'),1.57,.35,views=('front','left','three_quarter'),resolution=(500,500))
(p/'work/surface_repairs.json').write_text(json.dumps({'hem_vertices':changed,'head_holes_filled':filled,'retained_eye_mouth_boundary_edges':len(remaining),'forehead_boundary_edges':0,'reason':'False lower radial samples hit shoe geometry; nonmanifold nose anchor created facial punctures.'},indent=2))
