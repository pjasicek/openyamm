"""Measure a softer LOD0 reduction and the lower meshes at their actual switch sizes."""
import bpy,sys,runpy,json,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import round1_reduce_mesh as D
ctx=runpy.run_path(str(P/'scripts/round1_reduction_curve.py'),init_globals={'LEVELS':[]})
render=ctx['render'];R=P/'review/round1/reduction';W=P/'work/reduction'
curve=json.loads((R/'curve.json').read_text());curve['steps']=[x for x in curve['steps'] if x['level']==0];curve['selected']=curve['selected'][:1]
def savecurve():(R/'curve.json').write_text(json.dumps(curve,indent=2))
def reduce(path,dest,counts,level):
 bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();out={}
 for name,count in counts.items():out[name]=D.reduce(bpy.data.objects[name],r,count/D.triangles(bpy.data.objects[name]),level,soft=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(dest));return out
def metric(ref,folder):
 f=folder/'metrics.json';subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_reduce_metric.py'),str(ref),str(folder),str(f)],check=True);return json.loads(f.read_text())
best=P/'work/round1_lod0.blend'
for step in ([] if globals().get('SKIP_LOD0') else range(1,20)):
 bpy.ops.wm.open_mainfile(filepath=str(best));target=int(D.triangles(bpy.data.objects['Body'])*.9);dest=W/f'L0_soft_{step}.blend';counts=reduce(best,dest,{'Body':target},0);folder=R/f'L0_soft_{step}';folder.mkdir(exist_ok=True)
 runpy.run_path(str(P/'scripts/round1_rebake.py'),init_globals={'INPUT':str(dest.relative_to(P)),'OUTPUT':str(dest.relative_to(P)),'TEXTURES':str((folder/'textures').relative_to(P)),'REPORT':str((folder/'rebake.json').relative_to(P)),'ONLY':'Body'})
 render(folder,'Body',0,directory=folder/'textures');v=metric(R/'L0_Body_reference',folder);entry={'level':0,'object':'Body','method':'soft protected collapse','step':step,**counts['Body'],'min_iou':v['min_iou'],'min_ssim':v['min_ssim'],'visual_pass':v['pass'],'blend':str(dest.relative_to(P))}
 sys.argv=['gate','--',str(dest.relative_to(P))];runpy.run_path(str(P/'scripts/rig_gates_48.py'));g=json.loads((P/'review/rig_gates.json').read_text());shutil.copy2(P/'review/rig_gates.json',folder/'rig_gates.json')
 runpy.run_path(str(P/'scripts/round1_precision.py'),init_globals={'INPUT':str(dest.relative_to(P)),'REPORT':str((folder/'precision.json').relative_to(P))});pr=json.loads((folder/'precision.json').read_text());entry['rig_pass']=all(all(x['pass'].values()) for x in g.values()) and all(x['pass'] for x in pr.values());entry['failing_clips']=[n for n,x in g.items() if not all(x['pass'].values())]+[n for n,x in pr.items() if not x['pass']];entry['pass']=entry['visual_pass'] and entry['rig_pass'];curve['steps'].append(entry);savecurve();print('SOFT PROBE',entry,flush=True)
 if not entry['pass']:break
 best=dest
else:
 if not globals().get('SKIP_LOD0'):raise AssertionError('No stopping point')
if best!=P/'work/round1_lod0.blend':
 bpy.ops.wm.open_mainfile(filepath=str(best));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_lod0.blend'));curve['selected'][0]={'level':0,'blend':'work/round1_lod0.blend','body_triangles':D.triangles(bpy.data.objects['Body']),'axe_triangles':D.triangles(bpy.data.objects['AxeMesh'])};runpy.run_path(str(P/'scripts/round1_rebake.py'))
savecurve();base=P/'work/round1_lod0.blend';b0=curve['selected'][0]['body_triangles'];a0=curve['selected'][0]['axe_triangles']
for level,bcap,acap in [(1,min(6195,int(b0*.55)),min(1194,int(a0*.55))),(2,min(2229,int(b0*.25)),min(430,int(a0*.25))),(3,min(739,int(b0*.10)),min(135,int(a0*.10)))]:
 ref=R/f'L{level}_combined_reference';bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_high.blend'));render(ref,'Combined',level);best=None
 for step in range(12):
  counts={'Body':int(bcap*.90**step),'AxeMesh':int(acap*.90**step)};dest=W/f'L{level}_measured_{step}.blend';info=reduce(base,dest,counts,level);folder=R/f'L{level}_combined_{step}';render(folder,'Combined',level,directory=P/'textures/round1_rebaked');v=metric(ref,folder);entry={'level':level,'step':step,'object':'Combined','body_triangles':info['Body']['after'],'axe_triangles':info['AxeMesh']['after'],'pooled_iou':v['pooled_iou'],'min_iou':v['min_iou'],'min_ssim':v['min_ssim'],'pass':v['pooled_iou']>=.97,'blend':str(dest.relative_to(P))};curve['steps'].append(entry);savecurve();print('DISTANCE LOD',entry,flush=True)
  if not entry['pass']:
   assert best is not None,('Switch-size silhouette fails at installed count ceiling',entry)
   break
  best=dest
 else:raise AssertionError('No measured lower-LOD stopping point')
 bpy.ops.wm.open_mainfile(filepath=str(best));out=P/f'work/round1_lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));curve['selected'].append({'level':level,'blend':str(out.relative_to(P)),'body_triangles':D.triangles(bpy.data.objects['Body']),'axe_triangles':D.triangles(bpy.data.objects['AxeMesh'])});savecurve()
assert len(curve['selected'])==4
assert all(a['body_triangles']>b['body_triangles'] and a['axe_triangles']>b['axe_triangles'] for a,b in zip(curve['selected'],curve['selected'][1:]))
