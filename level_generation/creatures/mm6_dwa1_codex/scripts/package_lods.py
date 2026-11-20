from pathlib import Path
import sys,runpy,json,hashlib
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
def run(path,args):sys.argv=[str(path),*map(str,args)];runpy.run_path(str(path),run_name='__main__')
run(P/'scripts/shrink_shadow_lods.py',[P/'export/mm6_dwa1_lods.glb',P/'work/lods_shadow.glb'])
run(P.parent/'claude_shared/region_variants.py',[P/'work/lods_shadow.glb',P/'work/tiers_combined.glb',P/'textures/dwa1_ramps.json','--extra','Dwarf','openyamm_specular_mask=true','--extra','Dwarf','openyamm_specular=1','--extra','Dwarf','pbr.metallicFactor=0'])
run(ROOT/'tools/split_attachment.py',[P/'work/tiers_combined.glb','--joint','Axe','--body',P/'work/body_final_unvalidated.glb','--attachment',P/'export/mm6_dwa1_axe.glb'])
run(ROOT/'tools/merge_head_material.py',[P/'work/body_final_unvalidated.glb',P/'work/body_final_unvalidated.glb'])
run(P/'scripts/normalize_lod_weights.py',[P/'work/body_final_unvalidated.glb',P/'export/mm6_dwa1.glb'])
run(P/'scripts/viewer_tiers.py',[])
f=P/'review/viewer/manifest.json';m=json.loads(f.read_text())
for model in m['models']:
 path=P/'review/viewer'/f"mm6_{model['id']}.glb";sha=hashlib.sha256(path.read_bytes()).hexdigest();model.update(sha256=sha,url=path.name+'?v='+sha[:12])
f.write_text(json.dumps(m,indent=2))
