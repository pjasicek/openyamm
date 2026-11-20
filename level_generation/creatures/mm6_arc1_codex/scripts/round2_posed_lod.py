import bpy,sys,json,subprocess,os,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));from round2_reduce import reset,reduce,render
D=P/'review/round2/reduction';W=P/'work/round2';bpy.ops.wm.open_mainfile(filepath=str(W/'body_l3_fitted.blend'));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();world=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear();data=json.loads((W/'fit_input.json').read_text());out=json.loads((W/'fit_output.json').read_text());predict=np.array(data['world'])+np.einsum('vij,vj->vi',np.array(data['transforms']),np.array(out['rest'])-np.array(data['rest']));print('FIT MATRIX ERROR',np.linalg.norm(world-predict,axis=1).max(),[(m.name,m.type,getattr(m,'use_deform_preserve_volume',None))for m in ob.modifiers],flush=True)
rows=[]
for factor in [0,1,5]:
 ob,rig=reset('body');a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=[v.co.copy()for v in me.vertices];ev.to_mesh_clear();matrices={g.name:np.array(rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted())for g in ob.vertex_groups}
 for v,co in zip(ob.data.vertices,coords):v.co=co
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();os.environ['ARC1_LOD_PROTECT_FACTOR']=str(factor);count,protection=reduce(ob,rig,'body',3,603.1/10564);names={g.index:g.name for g in ob.vertex_groups}
 for v in ob.data.vertices:
  mat=sum((matrices[names[g.group]]*g.weight for g in v.groups),np.zeros((4,4)));v.co=(np.linalg.inv(mat)@np.r_[v.co,1])[:3]
 ob.data.update();tag=f'body_l3_posed{factor}';path=W/f'{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));render(ob,rig,'body',3,tag,P/'work/round2/metric_tiers/baked/arc1_a');result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(D),'body_l3_arc1_a_high',tag],text=True));row={'part':'body','lod':3,'triangles':count,'blend':str(path.relative_to(P)),**result};rows.append(row);(D/'distance_posed.json').write_text(json.dumps(rows,indent=2));print('POSED_REDUCTION',factor,count,result['pooled_iou'],flush=True)
