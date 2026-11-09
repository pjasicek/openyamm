"""Driver for motion revisions after texturing: re-author from the fidget onward (fidget, timing, wrists, twist,
dagger bone, dress cloth), copy every clip into the textured master (sync_actions.py; mesh, UVs and weights
untouched), separate the sleeve ruffles from the dress (fix_cuffs.py) and export LOD0. Run compose_textures.py and,
afterwards, build_runtime.py with plain python3."""
import runpy, sys, os
from pathlib import Path
P = Path(__file__).resolve().parents[1]
def run(n, *args):
    sys.argv = [n, '--', *[str(x) for x in args]]
    runpy.run_path(str(P / 'scripts' / n), run_name='__main__')
W = P / 'work'
run('author_fidget.py')
run('finish_timing.py')
run('settle_wrists.py')
os.environ['FA'] = '0.6'; os.environ['FA_RAMP'] = '0.15,0.85'
run('twist_bones.py', W / 'rig_wrists.blend', W / 'rig_timed_twist.blend')
run('dagger.py')
run('dress_sim.py', W / 'rig_props.blend', W / 'rig_sim.blend')
run('sync_actions.py', W / 'rig_sim.blend', W / 'rig_textured_uv.blend')
run('sync_dagger_bone.py')
run('fix_cuffs.py')
run('fix_legs.py')
run('export_runtime.py')
