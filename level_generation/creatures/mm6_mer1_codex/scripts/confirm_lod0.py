import bpy,sys,json,runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import search_reduction as S,reduction_common as C,reduction_bake as B
f=P/'review/reduction/body_lod0_curve.json';d=json.loads(f.read_text());row=d['steps'][-1];sys.argv=['candidate_prop.py','--',row['blend'],'body_lod0_s4_verified'];runpy.run_path(str(P/'scripts/candidate_prop.py'),run_name='__main__');pr=json.loads((P/'review/body_lod0_s4_verified_prop.json').read_text());row['gates']['prop_penetration_mm']=max(x['head_body_penetration_mm']for x in pr.values());row['gates']['pass']=row['gates']['prop_penetration_mm']<2;row['pass']=row['gates']['pass']and row['visual']['pass']
if row['pass']:d['accepted']=row['blend']
f.write_text(json.dumps(d,indent=2));print('CONFIRMED',row['pass'],flush=True)
if row['pass']:
 bpy.ops.wm.open_mainfile(filepath=str(P/row['blend']));C.reset();obj=bpy.data.objects['Body'];C.reduce(obj,.9);tex=P/'work/reduction/body_lod0_5_textures';B.bake(obj,tex);subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_previews.py'),str(tex)],check=True);dest=P/'work/reduction/body_lod0_5.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=P/'review/reduction/body_lod0/step_05';S.render(folder,'body',0,tex);v=S.metrics(P/'review/reduction/body_lod0/reference',folder);n={'step':5,'triangles':C.triangles(obj),'blend':str(dest.relative_to(P)),'textures':str(tex.relative_to(P)),'visual':v}
 if v['pass']:n['gates']=S.gates(dest,'body_lod0_s5')
 n['pass']=v['pass']and n.get('gates',{}).get('pass',False);d['steps'].append(n)
 if n['pass']:d['accepted']=n['blend']
 f.write_text(json.dumps(d,indent=2));print('FINAL NEAR STEP',n['triangles'],v['min_iou'],v['min_ssim'],n['pass'],flush=True)
