import bpy,sys,math,json,subprocess
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,search_reduction as S,reduction_bake as B
W=P/'work/reduction';O=P/'review/reduction';rows=[]
N=10
profile=[(-.061,.014),(-.045,.022),(-.022,.0125),(.08,.015),(.15,.019),(.25,.033),(.33,.05),(.39,.0545),(.425,.043),(.445,.023)]
for index,(phase,gain)in enumerate([(phase,gain)for phase in [0,math.pi/N/2,math.pi/N]for gain in [1,1.025]]):
 bpy.ops.wm.open_mainfile(filepath=str(W/'club_lod0_2_final.blend'));C.reset();o=bpy.data.objects['ClubMesh'];r=bpy.data.objects['Rig'];bone=r.data.bones['Club'];M=(bone.tail_local-bone.head_local).normalized().to_track_quat('Z','Y').to_matrix().to_4x4();M.translation=bone.head_local;verts=[]
 for z,rad in profile:
  for j in range(N):
   a=j*2*math.pi/N+phase;rr=rad*gain*(1+.025*math.sin(a*3+z*9)+.015*math.cos(a*7-z*5));verts.append(M@Vector((rr*math.cos(a),rr*math.sin(a),z)))
 tip=len(verts);verts.append(M@Vector((0,0,.452)));bottom=len(verts);verts.append(M@Vector((0,0,-.065)));faces=[]
 for i in range(len(profile)-1):
  for j in range(N):
   a=i*N+j;b=i*N+(j+1)%N;c=(i+1)*N+(j+1)%N;d=(i+1)*N+j;faces.extend([(a,b,c),(a,c,d)])
 for j in range(N):faces.append(((j+1)%N,j,bottom))
 for j in range(N):faces.append(((len(profile)-1)*N+j,(len(profile)-1)*N+(j+1)%N,tip))
 me=bpy.data.meshes.new('Far club silhouette');me.from_pydata(verts,[],faces);me.update();me.uv_layers.new(name='UVMap');me.materials.append(o.data.materials[0]);o.data=me;o.vertex_groups.clear();o.vertex_groups.new(name='Club').add(list(range(len(verts))),1,'REPLACE')
 for f in me.polygons:f.use_smooth=True
 dest=W/f'club_lod3_200_profile_{index}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=O/f'club_lod3/200_profile_{index}';S.render(folder,'club',3);v=S.metrics(O/'club_lod3/reference_final',folder);rs=list(v['views'].values());inter=sum(x['iou']*(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rs);v['pooled_iou']=inter/(sum(x['reference_pixels']+x['candidate_pixels']for x in rs)-inter);v['pass']=v['pooled_iou']>=.97
 row={'step':index,'triangles':C.triangles(o),'blend':str(dest.relative_to(P)),'renders':str(folder.relative_to(P)),'visual':v,'pass':False,'method':'profile-preserving 10-sided lathe, ten rings and rounded end caps','phase':phase,'radius_gain':gain};rows.append(row);print('CLUB FAR PROFILE',index,v['pooled_iou'],flush=True)
accepted=None
for row in sorted(rows,key=lambda r:-r['visual']['pooled_iou']):
 if not row['visual']['pass']:continue
 bpy.ops.wm.open_mainfile(filepath=str(P/row['blend']));C.reset();o=bpy.data.objects['ClubMesh'];tex=W/f'club_lod3_200_profile_{row["step"]}_textures';B.bake(o,tex);bpy.ops.wm.save_as_mainfile(filepath=str(P/row['blend']));S.render(P/row['renders'],'club',3);v=S.metrics(O/'club_lod3/reference_final',P/row['renders']);rs=list(v['views'].values());inter=sum(x['iou']*(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rs);v['pooled_iou']=inter/(sum(x['reference_pixels']+x['candidate_pixels']for x in rs)-inter);v['pass']=v['pooled_iou']>=.97;row['visual']=v;row['textures']=str(tex.relative_to(P));row['gates']=S.gates(P/row['blend'],f'club_lod3_200_profile{row["step"]}');row['pass']=v['pass']and row['gates']['pass']
 if row['pass']:accepted={k:row[k]for k in ['blend','textures','triangles']};break
(O/'club_lod3_curve.json').write_text(json.dumps({'kind':'club','level':3,'steps':rows,'accepted':accepted['blend']if accepted else None,'camera':{'switch_pixels':88},'thresholds':{'pooled_iou':.97}},indent=2))
assert accepted,'No valid far club profile'
selection=json.loads((O/'selection_partial.json').read_text());selection['club']=selection['club'][:3]+[accepted];(O/'selection.json').write_text(json.dumps(selection,indent=2));print('FINAL SELECTION',json.dumps(selection),flush=True)
