import bpy,sys,json,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import round4_search as S
report={}
for level in range(4):
 ref=P/'work/round4'/f'body_lod{level}_0.blend';bpy.ops.wm.open_mainfile(filepath=str(ref));S.activate('Standing');axe=bpy.data.objects['Axe'];ev=axe.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([tuple(axe.matrix_world@v.co)for v in mesh.vertices]);ev.to_mesh_clear();center=((co.min(0)+co.max(0))/2).tolist()
 blend=P/'work/export_reimport.blend'if level==0 else P/f'work/round4/final_lod{level}.blend'
 for kind in ['body','axe']:
  tag=f'{kind}_lod{level}';curve=json.loads((S.OUT/f'{tag}_curve.json').read_text());S.CALIBRATION.clear();S.CALIBRATION.update(diameter=curve['camera']['bound_diameter_m'],axe_center=center)
  bpy.ops.wm.open_mainfile(filepath=str(blend));S.cleanup();folder=S.OUT/tag/'final_export';camera=S.render(folder,kind,level);metrics=S.evaluate(S.OUT/tag/'reference',folder)
  report[tag]={'camera':camera,'metrics':metrics};print('FINAL_VISUAL',tag,metrics['min_iou'],metrics['min_ssim'],metrics['pass'],flush=True)
out={'runtime_sha256':hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest(),'axe_sha256':hashlib.sha256((P/'export/mm6_dwa1_axe.glb').read_bytes()).hexdigest(),'reference':'Each accepted round 3 colour LOD before reduction, at its actual viewer/switch distance; four body poses x eight views and eight prop views.','levels':report,'pass':all(x['metrics']['pass']for x in report.values())}
(S.OUT/'final_visual.json').write_text(json.dumps(out,indent=2)+'\n');assert out['pass']

