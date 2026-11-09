"""Spend the remaining far-LOD budget on the most curved visible silhouette edges."""
import bpy,bmesh,json,math,os,runpy,sys,subprocess
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];R=P/'review/round3';D=R/'far_refined88';D.mkdir(exist_ok=True);sys.path.insert(0,str(P/'scripts'));import compare_exported_lods as C
C.O=D/'renders';C.O.mkdir(exist_ok=True);C.PHYSICAL=False;C.TIER_DIR=R/'reference_tier_textures';C.cal['body_diameter_m']=1.763883397
def pose():
 rig=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);bpy.context.view_layer.update();return rig
bpy.ops.wm.open_mainfile(filepath=str(R/'before/work/final_motion.blend'));pose();high={}
for name in ['Body','Axe','Shield']:
 ob=bpy.data.objects[name];me=ob.data;me.calc_loop_triangles();rest=[v.co.copy() for v in me.vertices];weights=[{ob.vertex_groups[g.group].name:g.weight for g in v.groups} for v in me.vertices];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=[ob.matrix_world@v.co for v in em.vertices];ev.to_mesh_clear();pv=[x.value for x in me.attributes['piece'].data] if 'piece' in me.attributes else [0]*len(rest);groups={}
 for f in me.loop_triangles:groups.setdefault(pv[f.vertices[0]],[]).append(tuple(f.vertices))
 high[name]=(rest,weights,co,{k:(BVHTree.FromPolygons(co,fs,all_triangles=True),fs) for k,fs in groups.items()})
records=[]
for count in [22]:
 bpy.ops.wm.open_mainfile(filepath=str(R/'far_repaired/lod3.blend'));rig=pose();ranked=[];data={}
 for name in ['Body','Axe','Shield']:
  ob=bpy.data.objects[name];names=[g.name for g in ob.vertex_groups];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=[ob.matrix_world@v.co for v in me.vertices];bm=bmesh.new();bm.from_mesh(me);bm.normal_update();tree=BVHTree.FromBMesh(bm);ev.to_mesh_clear();seen={};pv=[a.value for a in ob.data.attributes['piece'].data] if 'piece' in ob.data.attributes else [0]*len(co)
  for j in range(8):
   d=Vector((math.sin(j*math.pi/4),-math.cos(j*math.pi/4),.08)).normalized()
   for e in bm.edges:
    if len(e.link_faces)!=2:continue
    ns=[f.normal.dot(d) for f in e.link_faces]
    if not min(ns)<=0<=max(ns):continue
    a,b=[v.index for v in e.verts];mid=(co[a]+co[b])*.5;hit=tree.ray_cast(mid+d*4,-d,8)[0];n=d.cross(co[b]-co[a]).normalized()
    if hit is None or (hit-mid).length>.003 or not any(tree.ray_cast(mid+n*(s*.003)+d*4,-d,8)[0] is None for s in [-1,1]):continue
    if any(any(('Hand' in names[g.group] or 'Finger' in names[g.group]) and g.weight>.3 for g in ob.data.vertices[i].groups) for i in [a,b]):continue
    key=tuple(sorted((a,b)));seen[key]=seen.get(key,0)+1
  for (a,b),views in seen.items():
   part=pv[a];part=part if part in high[name][3] else next(iter(high[name][3]));tree2,faces=high[name][3][part];hit,n,fi,d=tree2.find_nearest((co[a]+co[b])*.5);score=d*(co[b]-co[a]).length*views;ranked.append((score,name,a,b,part))
  bm.free();data[name]=(co,names)
 used=set();chosen=[]
 for row in sorted(ranked,reverse=True):
  score,name,a,b,part=row
  if (name,a) in used or (name,b) in used:continue
  chosen.append(row);used.update([(name,a),(name,b)])
  if len(chosen)==count:break
 for name in ['Body','Axe','Shield']:
  ob=bpy.data.objects[name];names=data[name][1];bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();deform=bm.verts.layers.deform.active;pieces=bm.verts.layers.int.get('piece');old=set(bm.verts);pairs={tuple(sorted((a,b))) for _,n,a,b,_ in chosen if n==name};edges=[e for e in bm.edges if tuple(sorted(v.index for v in e.verts)) in pairs]
  if not edges:bm.free();continue
  bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=False);matrices={b.name:rig.matrix_world@b.matrix@rig.data.bones[b.name].matrix_local.inverted() for b in rig.pose.bones};rest,weights,co,trees=high[name]
  bm.to_mesh(ob.data);bm.free();ob.data.update()
 tris=sum(sum(len(f.vertices)-2 for f in bpy.data.objects[n].data.polygons) for n in ['Body','Axe','Shield']);assert tris<=924;path=D/f'splits_{count}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));E=D/f'export_{count}';os.environ.update(FIGC_EXPORT_SOURCE=str(path),FIGC_EXPORT_DIR=str(E));runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');folder=C.render(E/'mm6_figc_lod0.glb',3,f'splits_{count}');mp=D/f'metrics_{count}.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/measure_reduction.py'),str(R/'switch_height/reference_lod3'),str(folder),str(mp)],check=True);m=json.loads(mp.read_text());pooled=sum(v['iou']*v['reference_foreground_pixels'] for v in m['views'])/sum(v['reference_foreground_pixels'] for v in m['views']);row={'splits':count,'triangles':tris,'pooled_iou':pooled,'minimum_iou':m['minimum_iou'],'blend':str(path.relative_to(P))};records.append(row);(D/'curve.json').write_text(json.dumps(records,indent=2));print('FAR_REFINED',row,flush=True)
