import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import silhouette_round3 as S
old=S.old;old.R=R;curve=json.loads((R/'silhouette_curve.json').read_text());h=curve[0]['body_standing_height_m'];pixels=2.1778047/h*700
for factor in [1.,.01]:
 for step in [5,6,7,8,9,10]:
  body,rig=old.reset(0);ratio=.9**step;prot=S.reduce(body,rig,1.,factor)
  vg=body.vertex_groups.new(name='_protect')
  # Make the requested protected regions fully protected, not fractional candidates.
  tmp=old.protect(body,rig,0);group=body.vertex_groups['_protect.001'];idx=group.index
  ids=[v.index for v in body.data.vertices if any(e.group==idx and e.weight>=.8 for e in v.groups)]
  body.vertex_groups.remove(group);vg.add(ids,1.,'REPLACE')
  md=body.modifiers.new('Binary protected collapse','DECIMATE');md.ratio=ratio;md.use_collapse_triangulate=True;md.vertex_group='_protect';md.invert_vertex_group=True;md.vertex_group_factor=factor;bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name);body.vertex_groups.remove(body.vertex_groups['_protect']);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
  count=sum(len(p.vertices)-2 for p in body.data.polygons);tag=f'binary{factor}_s{step:02d}';rig.animation_data.action=None
  for bone in rig.pose.bones:bone.matrix_basis.identity()
  bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));old.render(body,rig,tag,pixels)
  metrics=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics_round2.py'),str(R),'high_silhouette',tag],text=True));row={'tag':tag,'ratio':ratio,'triangles':count,'min_iou':metrics['min_iou'],'views':[x['iou']for x in metrics['views']],'silhouette_pass':metrics['min_iou']>=.99,'actor_height_px':700,'body_standing_height_m':h,'protection_strength':factor,'protection':prot,'blend':f'work/round3/{tag}.blend'};curve.append(row);(R/'silhouette_curve.json').write_text(json.dumps(curve,indent=2));print('SILHOUETTE',tag,count,row['min_iou'],flush=True)
  if not row['silhouette_pass']:break
