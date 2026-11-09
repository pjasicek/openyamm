import sys,bpy,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduce_round2 as red
rows=[]
for factor in [.001,.01,.1,1]:
 body,rig=red.reset();red.protect(body,rig,0);md=body.modifiers.new('Collapse','DECIMATE');md.ratio=.9;md.use_collapse_triangulate=True;md.vertex_group='_protect';md.invert_vertex_group=True;md.vertex_group_factor=factor;bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name)
 tag=f'probe_factor{factor}';red.render(body,rig,tag,800);r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics_round2.py'),str(red.R),'body_l0_reference',tag],text=True));rows.append({'factor':factor,**r});print('PROBE',factor,r['min_iou'],r['min_ssim'],flush=True)
(red.R/'protection_probe.json').write_text(json.dumps(rows,indent=2))
