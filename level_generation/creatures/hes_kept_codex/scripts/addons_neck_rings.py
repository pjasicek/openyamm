"""Put topology rings at the rigid neck band's limits so long triangles cannot fold through its liner."""
import bpy,bmesh,sys,os,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];b=bpy.data.objects['Kept'];r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
bm=bmesh.new();bm.from_mesh(b.data);pc=bm.verts.layers.int.get('piece');deform=bm.verts.layers.deform.verify();idx=b.vertex_groups['Kept_Collar'].index;before=(len(bm.verts),len(bm.faces))
for z in (1.38,1.505):
 vs=[v for v in bm.verts if v[pc]==1];es=[e for e in bm.edges if all(v[pc]==1 for v in e.verts)];fs=[f for f in bm.faces if all(v[pc]==1 for v in f.verts)]
 result=bmesh.ops.bisect_plane(bm,geom=vs+es+fs,dist=1e-7,plane_co=(0,0,z),plane_no=(0,0,1),clear_outer=False,clear_inner=False)
 for e in result['geom_cut']:
  if isinstance(e,bmesh.types.BMVert):e[pc]=1
for v in bm.verts:
 if v[pc]==1 and 1.38-1e-6<=v.co.z<=1.505+1e-6:
  v[deform].clear();v[deform][idx]=1.
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));after=(len(bm.verts),len(bm.faces));bm.to_mesh(b.data);bm.free()
report={'before':before,'after':after,'full_rigid_skin_band_z_m':[1.38,1.505],'purpose':'local topology at covered neck prevents spanning triangles from interpolating across the rigid band','freed_unchanged':True};(P/'review/addons_v2/neck_topology.json').write_text(json.dumps(report,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(path));print('NECK_RINGS',report,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
