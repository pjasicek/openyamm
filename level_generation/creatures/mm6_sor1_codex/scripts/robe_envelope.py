"""Remove inward radial folds inherited from the fused generated robe/shoe geometry."""
import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_head2_uv.blend'));body=bpy.data.objects['Body'];me=body.data
changes=[];before=[];after=[]
for v in me.vertices:
 if me.attributes['piece'].data[v.index].value!=100:continue
 x,y,z=v.co;rx=float(np.interp(z,[.125,.3,.6,.95,1.09],[.30,.28,.245,.205,.17]));ry=float(np.interp(z,[.125,.3,.6,.95,1.09],[.255,.235,.205,.155,.12]));rho=((x/rx)**2+((y+.02)/ry)**2)**.5
 before.append(rho);target=float(np.clip(rho,.94,1.06));blend=float(np.clip((1.085-z)/.07,0,1));factor=1+blend*(target/max(rho,1e-6)-1);old=v.co.copy();v.co.x*=factor;v.co.y=(y+.02)*factor-.02;changes.append((v.co-old).length);after.append(rho*factor)
report={'vertices':len(changes),'max_displacement_mm':max(changes)*1000,'mean_displacement_mm':float(np.mean(changes)*1000),'rho_before':[min(before),max(before)],'rho_after':[min(after),max(after)],'reason':'Native tapered robe envelope, shallow folds; original inner valleys followed the fused shoes and legs.'}
(p/'work/robe_envelope.json').write_text(json.dumps(report,indent=2));print('ENVELOPE',report)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_robe_envelope.blend'))
