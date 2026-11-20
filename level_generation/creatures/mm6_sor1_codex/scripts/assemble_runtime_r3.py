from pathlib import Path
import subprocess,sys,json,hashlib,struct
p=Path(__file__).resolve().parents[1];repo=p.parents[2];e=p/'export';log=[]
def run(*args):
 r=subprocess.run([sys.executable,*map(str,args)],check=True,capture_output=True,text=True);log.append(r.stdout+r.stderr);print(r.stdout)
run(p.parent/'claude_shared/region_variants.py',e/'mm6_sor1_lods.glb',e/'mm6_sor1.glb',p/'textures/round3/ramps.json','--extra','Sorcerer','openyamm_specular=0','--extra','Sorcerer','pbr.metallicFactor=0','--extra','SorcererStaff','openyamm_specular=1','--extra','SorcererStaff','openyamm_specular_mask=true')
run(repo/'tools/split_attachment.py',e/'mm6_sor1.glb','--joint','B_Staff','--body',e/'mm6_sor1.glb','--attachment',e/'mm6_sor1_staff.glb')
run(p/'scripts/staff_material_lods_r3.py')
run(p/'scripts/merge_head_lods_r3.py',e/'mm6_sor1.glb',e/'mm6_sor1.glb')
run(p/'scripts/viewer_tiers_r3.py')
(p/'work/assemble_runtime.log').write_text(''.join(log))
