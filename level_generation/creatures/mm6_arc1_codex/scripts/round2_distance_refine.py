import bpy,sys,json,subprocess,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round2_reduce import reset,reduce,render
D=P/'review/round2/reduction';rows=[]
for factor in [0,.1,.5,1,20]:
 os.environ['ARC1_LOD_PROTECT_FACTOR']=str(factor)
 ob,rig=reset('body');actual,protection=reduce(ob,rig,'body',3,603.1/10564);tag=f'body_l3_factor{factor}';path=P/f'work/round2/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));render(ob,rig,'body',3,tag,P/'work/round2/metric_tiers/baked/arc1_a')
 result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(D),'body_l3_arc1_a_high',tag],text=True));row={'part':'body','lod':3,'triangles':actual,'factor':factor,'blend':str(path.relative_to(P)),**result};rows.append(row);(D/'distance_refine.json').write_text(json.dumps(rows,indent=2));print('REFINE',factor,actual,result['pooled_iou'],flush=True)
