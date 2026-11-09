import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from g6_head_clearance import Clearance
from volume_contact import volumes,deepest
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rebake/runtime_lod3.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(13,subframe=.125);c=Clearance(b);old=c.measure();ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();xyz=np.array([tuple(b.matrix_world@v.co)for v in m.vertices]);ev.to_mesh_clear();side=old[2];polys=[list(p.vertices)for p in c.side[side]];head=xyz[c.head[::2]];bounded=deepest(volumes(xyz,polys,c.pv),head);point=xyz[c.last_hit[2]];groups=volumes(xyz,polys,c.pv);boxes=[]
for piece,center,axes,lo,hi,_,_ in groups:
 q=(point-center)@axes.T;boxes.append({'piece':piece,'point_local':q.tolist(),'lo':lo.tolist(),'hi':hi.tolist(),'inside_obb':bool(np.all((q>=lo-1e-6)&(q<=hi+1e-6)))})
result={'old_nearest_plane_depth_m':old[0],'old_hit_piece_weight_vertex':c.last_hit,'head_point':point.tolist(),'bounded_volume_depth_m':bounded[0],'component_bounds':boxes}
(P/'review/rebake/head_plane_audit.json').write_text(json.dumps(result,indent=2));print('HEAD_AUDIT',result,flush=True)
