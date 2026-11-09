"""Build the production body, colour/shadow LODs, shared native tiers and separate rigid sword."""
from pathlib import Path
import runpy
import subprocess
import sys
p = Path(__file__).resolve().parents[1]
repo = p.parents[3]
runpy.run_path(str(p / 'scripts/settle_death.py'), run_name='__main__')
runpy.run_path(str(p / 'scripts/finish_delivery_floor.py'), run_name='__main__')
runpy.run_path(str(p / 'scripts/export_runtime.py'), run_name='__main__')


def run(script, *args):
    subprocess.run(['python3', str(repo / script), *map(str, args)], check=True)


run('tools/prepare_actor_glb.py', p / 'export/mm8_m404_lod0.glb', p / 'export/mm8_m404_runtime_lod0.glb')
sys.argv = ['build_actor_lods.py', '--', str(p / 'export/mm8_m404_runtime_lod0.glb'),
            str(p / 'export/mm8_m404_lods.glb'), '--mesh-node', 'M404', '--max-influences', '4']
runpy.run_path(str(repo / 'tools/build_actor_lods.py'), run_name='__main__')
subprocess.run(['python3', str(p / 'scripts/shrink_shadow_lods.py'), str(p / 'export/mm8_m404_lods.glb'),
                str(p / 'export/mm8_m404_lods_shadowfix.glb')], check=True)
run('level_generation/creatures/claude_shared/region_variants.py', p / 'export/mm8_m404_lods_shadowfix.glb',
    p / 'export/mm8_m404.glb', p / 'textures/m404_ramps.json',
    '--extra', 'M404', 'openyamm_specular=1', '--extra', 'M404', 'openyamm_specular_mask=true',
    '--extra', 'M404', 'pbr.metallicFactor=0', '--extra', 'Sword', 'openyamm_specular=1',
    '--extra', 'Sword', 'openyamm_specular_mask=true', '--extra', 'Sword', 'pbr.metallicFactor=0')
run('tools/split_attachment.py', p / 'export/mm8_m404.glb', '--joint', 'Socket_Sword',
    '--body', p / 'export/mm8_m404.glb', '--attachment', p / 'export/mm8_m404_sword.glb')
run('tools/merge_head_material.py', p / 'export/mm8_m404.glb', p / 'export/mm8_m404.glb')
print('RUNTIME_READY', p / 'export/mm8_m404.glb', flush=True)
