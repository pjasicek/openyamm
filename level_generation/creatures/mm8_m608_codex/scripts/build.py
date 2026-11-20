"""Build portable exports, shared variants, colour/shadow LODs and collapsed-mesh visibility."""
import bpy,runpy,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];E=P/'export'
def python(script,*args):subprocess.run(['/usr/bin/python3',str(script),*[str(a) for a in args]],check=True)
runpy.run_path(str(P/'scripts/shoulder_audit.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/export.py'),run_name='__main__')
python(R/'tools/prepare_actor_glb.py',E/'mm8_m608_lod0.glb',E/'mm8_m608_prepared.glb')
sys.path.insert(0,str(R/'tools'));from build_actor_lods import generate
for node,src,dst in [('Juggernaut','prepared','body_lods'),('Rubble','body_lods','lods')]:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 generate(E/f'mm8_m608_{src}.glb',E/f'mm8_m608_{dst}.glb',node,ratios=(.5,.25,.125),max_influences=4)
 (E/f'lods_{node.lower()}.json').write_text((E/'lods.json').read_text())
python(P.parent/'claude_shared/region_variants.py',E/'mm8_m608_lods.glb',E/'mm8_m608_variants.glb',P/'textures/juggernaut_ramps.json')
python(R/'tools/merge_head_material.py',E/'mm8_m608_variants.glb',E/'mm8_m608_merged.glb')
python(R/'tools/model_hide_collapsed_meshes.py',E/'mm8_m608_merged.glb','--write',E/'mm8_m608.glb')
python(P/'scripts/finish_runtime.py')
python(P/'scripts/fix_lod_normals.py')
python(P/'scripts/static_audit.py')

runpy.run_path(str(P/'scripts/audit.py'),run_name='__main__')
python(P/'scripts/setup_viewer.py')
