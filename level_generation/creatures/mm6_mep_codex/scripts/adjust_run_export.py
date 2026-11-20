import bpy,sys,runpy,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));from final_refinements import fit_running_stride,ground_running
bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm6_mep.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Mep'];ground_running(r,b);a=bpy.data.actions['Running'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;bounds=[]
for t in np.arange(0,.800001,1/48):
 f=t*30;sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();coords=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();bounds.append([coords.min(0),coords.max(0)])
info=json.loads((p/'export/export_info.json').read_text());info['clips']['Running']['bounds']=np.array(bounds)[:,0].min(0).tolist()+np.array(bounds)[:,1].max(0).tolist();info['locomotion']={'walking_stride_m':.34/.55,'running_stride_m':.34*1.55/.55,'runtime_running_multiplier':1.55};(p/'export/export_info.json').write_text(json.dumps(info,indent=2))
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();b.name='Body';bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/final_lod0.blend'));b.name='Mep';bpy.ops.wm.save_as_mainfile(filepath=str(p/'export/mm6_mep.blend'))
runpy.run_path(str(p/'scripts/reexport_animation.py'),run_name='__main__');runpy.run_path(str(p/'scripts/repair_review_actions.py'),run_name='__main__')
