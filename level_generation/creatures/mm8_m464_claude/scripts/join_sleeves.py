import bpy,bmesh,sys,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_mfp_codex/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/adapted_body.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];bm=bmesh.new();bm.from_mesh(b.data);piece=bm.verts.layers.int['piece'];report=[]
for side,sign,pid in [('L',1,4),('R',-1,5)]:
 S=r.data.bones[f'B_{side}_UpperArm'].head_local;E=r.data.bones[f'B_{side}_Forearm'].head_local;axis=(E-S).normalized();basis=axis.cross(Vector((0,1,0))).normalized();other=axis.cross(basis)
 rings=[]
 for part,cut,upper in [(0,.135,True),(pid,.175,False)]:
  def region(v):return v[piece]==part and (part!=0 or (v.co.x*sign>.10 and 1.13<v.co.z<1.35))
  faces=[f for f in bm.faces if all(region(v)for v in f.verts)];verts=set(v for f in faces for v in f.verts);edges=set(e for f in faces for e in f.edges)
  bmesh.ops.bisect_plane(bm,geom=list(verts)+list(edges)+faces,dist=1e-7,plane_co=S+axis*cut,plane_no=axis)
  dead=[v for v in bm.verts if region(v)and ((v.co-S).dot(axis)>cut+1e-6 if upper else (v.co-S).dot(axis)<cut-1e-6)]
  bmesh.ops.delete(bm,geom=dead,context='VERTS')
  ring=[v for v in bm.verts if region(v)and abs((v.co-S).dot(axis)-cut)<1e-5 and any(e.is_boundary for e in v.link_edges)]
  assert len(ring)>=6,(side,part,len(ring))
  ring.sort(key=lambda v:math.atan2((v.co-S).dot(other),(v.co-S).dot(basis)))
  for v in ring:
   radial=v.co-(S+axis*cut);v.co=S+axis*cut+radial.normalized()*(.047 if upper else .044)
  rings.append(ring)
 a,c=rings;i=j=0
 while i<len(a)or j<len(c):
  if (i+1)/len(a)<(j+1)/len(c):vs=[a[i%len(a)],a[(i+1)%len(a)],c[j%len(c)]];i+=1
  else:vs=[a[i%len(a)],c[(j+1)%len(c)],c[j%len(c)]];j+=1
  bm.faces.new(vs)
 report.append({'side':side,'ring_counts':[len(a),len(c)]})
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(b.data);bm.free()
for f in b.data.polygons:f.use_smooth=True
# Bridge endpoints retain interpolated arm weights and form one continuous closed sleeve surface.
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/garments.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(P/'review/garments'),.84,1.85,views=('front','left','back'),resolution=(650,900))
(P/'review/sleeve_joins.json').write_text(json.dumps(report,indent=2))
