import bpy,sys,runpy,json,subprocess
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));ctx=runpy.run_path(str(P/'scripts/round1_reduction_curve.py'),init_globals={'LEVELS':[]});render=ctx['render'];R=P/'review/round1/reduction';report=[]
for mm in [0,1,2,3,4,6,8]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction/L3_outline_fit_10.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
 for obj in [bpy.data.objects['Body'],bpy.data.objects['AxeMesh']]:
  e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();normals=[v.normal.copy() for v in me.vertices];e.to_mesh_clear();matrices={g.index:r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted() for g in obj.vertex_groups if g.name in r.pose.bones}
  for v in obj.data.vertices:
   S=Matrix(((0,0,0,0),)*4)
   for g in v.groups:
    if g.group in matrices:S+=matrices[g.group]*g.weight
   v.co+=S.to_3x3().inverted_safe()@normals[v.index]*(mm/1000)
  obj.data.update()
 bpy.context.view_layer.update();dest=P/f'work/reduction/L3_inflate_{mm}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=R/f'L3_inflate_{mm}';render(folder,'Combined',3,directory=P/'textures/round1_rebaked');subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_reduce_metric.py'),str(R/'L3_runtime_reference'),str(folder),str(folder/'metrics.json')],check=True);v=json.loads((folder/'metrics.json').read_text());entry={'level':3,'inflate_mm':mm,'blend':str(dest.relative_to(P)),'pooled_iou':v['pooled_iou'],'min_iou':v['min_iou'],'min_ssim':v['min_ssim'],'pass':v['pooled_iou']>=.97};report.append(entry);(R/'inflation_curve.json').write_text(json.dumps(report,indent=2));print('INFLATION',entry,flush=True)
