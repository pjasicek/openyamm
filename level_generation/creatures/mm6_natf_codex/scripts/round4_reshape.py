"""Round 4: slim only the skirt, carrying UVs and existing cloth weights."""
import bpy,json,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sel=json.loads((P/'review/round4/before/review/reduction_selected.json').read_text())
def slim(p):
 q=np.array(p,dtype=float);t=np.clip((1.0-q[...,2])/.27,0,1);t=t*t*(3-2*t);q[...,0]=-.006+(q[...,0]+.006)*(1-.28*t);return q
report={}
def reshape():
 rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 ob=bpy.data.objects['Body'];co=np.array([v.co[:]for v in ob.data.vertices]);mask=np.array([sum(g.weight for g in v.groups if ob.vertex_groups[g.group].name.startswith('Skirt_'))>.000001 for v in ob.data.vertices]);new=co.copy();new[mask]=slim(co[mask]);ob.data.vertices.foreach_set('co',new.flatten());ob.data.update()
 chains=json.loads(bpy.context.scene['natf_skirt'])
 for c in chains:c['points']=slim(c['points']).tolist()
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 for c in chains:
  for k,n in enumerate(c['bones']):
   b=rig.data.edit_bones[n];b.head=c['points'][k];b.tail=c['points'][k+1]
 bpy.ops.object.mode_set(mode='OBJECT');bpy.context.scene['natf_skirt']=json.dumps(chains)
 assert np.array_equal(co[~mask],new[~mask]);return {'vertices':int(mask.sum()),'before_width':float(np.ptp(co[mask,0])),'after_width':float(np.ptp(new[mask,0])),'uv_and_weights':'unchanged; cage refitted with same affine rest deformation'}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/sel['Body'][str(level)]['blend']));report[str(level)]=reshape();dst=f'work/round4_lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(P/dst));sel['Body'][str(level)]['blend']=dst
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round4/before/work/accepted_master.blend'));report['master']=reshape();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round4_rest.blend'))
(P/'review/reduction_selected.json').write_text(json.dumps(sel,indent=2));(P/'review/round4/rest_reshape.json').write_text(json.dumps(report,indent=2));print(report)
