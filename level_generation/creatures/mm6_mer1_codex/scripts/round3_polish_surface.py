import bpy,bmesh,sys,numpy as np,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/master.blend'));C.reset();o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];pv=np.array([a.value for a in o.data.attributes['piece'].data]);bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();part=bm.verts.layers.int['piece'];modified=[]
# Eye patches have open outer rims. Bury their rims under the surrounding eyelid surface.
for v in bm.verts:
 if v[part] in [14,15] and v.is_boundary:v.co.y+=.009;modified.append(v.index)
bm.to_mesh(o.data);bm.free()
names=[g.name for g in o.vertex_groups];W=np.zeros((len(pv),len(names)));co=np.array([v.co[:]for v in o.data.vertices]);adj=[[]for _ in pv]
for v in o.data.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
for e in o.data.edges:
 a,b=e.vertices
 if pv[a]==pv[b]==1:adj[a].append(b);adj[b].append(a)
for _ in range(8):
 old=W.copy()
 for i,nb in enumerate(adj):
  if nb and abs(co[i,0])>.17 and co[i,2]>1.05:W[i]=.65*old[i]+.35*old[nb].mean(0)
for i in np.where(pv==1)[0]:
 v=o.data.vertices[int(i)];sd='L'if v.co.x>0 else'R';wr=r.data.bones[f'B_{sd}_Hand'].head_local;axis=(wr-r.data.bones[f'B_{sd}_Forearm'].head_local).normalized();d=v.co-wr;along=d.dot(axis);rad=d-axis*along;t=float(np.clip((along+.075)/.045,0,1))if abs(v.co.x)>.37 else 0
 if t:
  t=t*t*(3-2*t);W[i]*=1-t;W[i,names.index(f'B_{sd}_Hand')]+=t
  if rad.length>.005:v.co+=rad.normalized()*(.006*t)
 for g in list(v.groups):o.vertex_groups[g.group].remove([int(i)])
 ids=np.argsort(W[i])[-4:];total=W[i,ids].sum()
 for j in ids:
  if W[i,j]>1e-8:o.vertex_groups[int(j)].add([int(i)],float(W[i,j]/total),'REPLACE')
C.reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/master.blend'));common.workbench_clay(bpy.context.scene,True);bpy.context.scene.display.shading.show_specular_highlight=False
C.activate('Standing');common.render_views(str(P/'review/round3/eye_fixed'),1.52,.43,views=('front','left','three_quarter'),resolution=(800,800));(P/'review/round3/eye_rim_fix.json').write_text(json.dumps({'recessed_eye_rim_vertices':modified,'depth_m':.009}))
