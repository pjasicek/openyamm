import bpy,sys,json,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import search_reduction as S,reduction_common as C,reduction_bake as B
W=P/'work/reduction';O=P/'review/reduction'
for kind,start in [('club',2)]:
 file=O/f'{kind}_lod0_curve.json';old=json.loads(file.read_text());backup=O/f'{kind}_lod0_curve_first_bake.json'
 if not backup.exists():shutil.copyfile(file,backup)
 else:old=json.loads(backup.read_text())
 cached=json.loads(file.read_text());bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'));C.cleanup();camera=old['camera']if (O/f'{kind}_lod0/reference_final').exists()else S.render(O/f'{kind}_lod0/reference_final',kind,0);rows=[];last=None
 for step in range(start,20 if kind=='body'else 4):
  if step==start:source=P/next(r['blend']for r in old['steps']if r['step']==step)
  else:source=last
  bpy.ops.wm.open_mainfile(filepath=str(source));C.reset();obj=bpy.data.objects['Body'if kind=='body'else'ClubMesh']
  if step>start:C.reduce(obj,.9)
  dest=W/f'{kind}_lod0_{step}_final.blend';tex=W/f'{kind}_lod0_{step}_final_textures';prior=next((r for r in cached['steps']if r.get('blend')==str(dest.relative_to(P))),None)
  if prior or dest.exists():
   bpy.ops.wm.open_mainfile(filepath=str(dest));C.reset();obj=bpy.data.objects['Body'if kind=='body'else'ClubMesh']
  else:B.bake(obj,tex)
  if kind=='body':subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_previews.py'),str(tex)],check=True)
  count=C.triangles(obj);bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=O/f'{kind}_lod0/step_{step:02}_final';S.render(folder,kind,0,tex if kind=='body'else None)if not prior else None;v=prior['visual']if prior else S.metrics(O/f'{kind}_lod0/reference_final',folder);row={'step':step,'triangles':count,'blend':str(dest.relative_to(P)),'textures':str(tex.relative_to(P)),'renders':str(folder.relative_to(P)),'visual':v}
  if v['pass']:row['gates']=S.gates(dest,f'{kind}_lod0_final{step}')
  row['pass']=v['pass']and row.get('gates',{}).get('pass',False);rows.append(row)
  if row['pass']:last=dest
  receipt={'kind':kind,'level':0,'before':old['before'],'reference':'work/reduction_master.blend','camera':camera,'protection':old['protection'],'preliminary_curve':str(backup.relative_to(P)),'steps':rows,'accepted':str(last.relative_to(P))if last else None,'rebake':'per-piece Cycles + nearest surface projection at open boundaries; full atlas coverage; native grey clasp'};file.write_text(json.dumps(receipt,indent=2));print('FINAL NEAR',kind,count,v['min_iou'],v['min_ssim'],row.get('gates'),row['pass'],flush=True)
  if not row['pass']:break
 assert last,(kind,'first clean candidate failed')
