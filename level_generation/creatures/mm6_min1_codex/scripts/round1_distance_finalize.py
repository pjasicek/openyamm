"""Fit the remaining distance chain at the renderer's actual projected switch sizes."""
import bpy,sys,runpy,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_reduce_mesh as D
R=P/'review/round1/reduction';W=P/'work/reduction'
render=runpy.run_path(str(P/'scripts/round1_reduction_curve.py'),init_globals={'LEVELS':[]})['render']
report=json.loads((R/'final_selection.json').read_text());report['fresh_lod2']=[]
def metric(ref,folder):
 subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_reduce_metric.py'),str(ref),str(folder),str(folder/'metrics.json')],check=True);return json.loads((folder/'metrics.json').read_text())
def freeze_motion():
 r=bpy.data.objects['Rig'];r.animation_data.action=None
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/production_master.blend'),link=False) as (src,dst):dst.actions=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
 for a in dst.actions:a.use_fake_user=True
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
# Regenerate with the current contour-protection method; the old L2 trials used the earlier mask.
best=None
for step in range(12):
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_master.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
 for name,cap in [('Body',1969),('AxeMesh',430)]:D.reduce(bpy.data.objects[name],r,int(cap*.9**step)/D.triangles(bpy.data.objects[name]),2,soft=True)
 dest=W/f'fresh_L2_{step}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=R/f'fresh_L2_{step}';render(folder,'Combined',2,directory=P/'textures/round1_rebaked');v=metric(R/'final_L2_reference',folder);row={'level':2,'body_triangles':D.triangles(bpy.data.objects['Body']),'axe_triangles':D.triangles(bpy.data.objects['AxeMesh']),'blend':str(dest.relative_to(P)),'pooled_iou':v['pooled_iou'],'min_ssim':v['min_ssim'],'pass':v['pooled_iou']>=.97};report['fresh_lod2'].append(row);(R/'final_selection.json').write_text(json.dumps(report,indent=2));print('FRESH LOD2',row,flush=True)
 if not row['pass']:break
 best=row
assert best is not None,'L2 cap needs contour fitting'
# Smallest measured L1 that keeps BOTH triangle chains strictly decreasing.
choices=[x for x in report['distance_steps'] if x['level']==1 and x['pass'] and x['body_triangles']>best['body_triangles'] and x['axe_triangles']>best['axe_triangles']]
assert choices
first=min(choices,key=lambda x:x['body_triangles']+x['axe_triangles']);selected=[first,best,report['selected'][2]]
for item in selected:
 bpy.ops.wm.open_mainfile(filepath=str(P/item['blend']));freeze_motion();bpy.ops.wm.save_as_mainfile(filepath=str(P/f"work/round1_lod{item['level']}.blend"))
# Verify the next L3 collapse: this protects against accepting the old installed ceiling as a target.
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_lod3.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
for name in ['Body','AxeMesh']:D.reduce(bpy.data.objects[name],r,.9,3,soft=True)
folder=R/'final_L3_next';render(folder,'Combined',3,directory=P/'textures/round1_rebaked');v=metric(R/'L3_runtime_reference',folder) if (R/'runtime_L3_reference').exists() else None
if v is None:
 bpy.ops.wm.save_as_mainfile(filepath=str(W/'final_L3_next.blend'));bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_high_final.blend'));ref=R/'final_L3_reference';render(ref,'Combined',3);v=metric(ref,folder)
report['lod3_next']={'pooled_iou':v['pooled_iou'],'min_ssim':v['min_ssim'],'pass':v['pooled_iou']>=.97}
assert not report['lod3_next']['pass'],'L3 still permits another reduction'
report['selected']=selected
assert all(a['body_triangles']>b['body_triangles'] and a['axe_triangles']>b['axe_triangles'] for a,b in zip(selected,selected[1:]))
(R/'final_selection.json').write_text(json.dumps(report,indent=2))
print('DISTANCE FINAL',selected,flush=True)
