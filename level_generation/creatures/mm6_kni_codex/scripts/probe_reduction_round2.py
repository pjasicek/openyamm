import sys,bpy,json,subprocess,bmesh
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduce_round2 as red
rows=[]
for mode in ['noop','weld_transfer','full_ratio1','unwelded_90']:
 body,rig=red.reset()
 if mode in ['weld_transfer','full_ratio1']:
  red.protect(body,rig,0)
  if mode=='full_ratio1':red.reduce(body,1.,0)
  else:
   bpy.context.view_layer.objects.active=body;md=body.modifiers.new('Carry','DATA_TRANSFER');md.object=bpy.data.objects['NormalReference'];md.use_loop_data=True;md.data_types_loops={'CUSTOM_NORMAL'};md.loop_mapping='POLYINTERP_NEAREST';md.use_object_transform=False;bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name)
 if mode=='unwelded_90':
  body.vertex_groups.new(name='_protect');md=body.modifiers.new('Collapse','DECIMATE');md.ratio=.9;md.use_collapse_triangulate=True;bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name)
 red.render(body,rig,'probe_'+mode,800);r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics_round2.py'),str(red.R),'body_l0_reference','probe_'+mode],text=True));rows.append({'mode':mode,'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),**r});print('PROBE',mode,r['min_iou'],r['min_ssim'],flush=True)
(red.R/'pipeline_probe.json').write_text(json.dumps(rows,indent=2))
