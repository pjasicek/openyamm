"""Run the existing map bake/minimap recipes and exit before Blender's host audio teardown hangs."""
import fcntl
import os
from pathlib import Path
import runpy
import sys
root = Path(__file__).resolve().parents[4]
mode = sys.argv[sys.argv.index('--') + 1]
assert mode in ('bake', 'minimap')
with (root/'output/hesper_stage/locks/stage.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_SH)
    if mode == 'bake':
        script = root/'tools/lighting/bake_outdoor.py'
        sys.argv = ['blender', '--', '--profile', str(root/'level_generation/projects/hesper_out1/bake_profile.json'),
                    '--output', str(root/'output/hesper_stage/bake_work/hesper_out1_gloamers_final'),
                    '--assets', str(root/'output/hesper_stage/assets_editor_dev'),
                    '--sources', str(root/'assets_source'), '--sources', str(root/'output/hesper_stage/sources')]
    else:
        script = root/'level_generation/projects/hesper_out1/build_minimap_blender.py'
        sys.argv = ['blender']
    try:
        runpy.run_path(str(script), run_name='__main__')
    except SystemExit as exit_status:
        if exit_status.code not in (None, 0):
            raise
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)
