"""Textured previews: the Doom Bug (bug_anim.blend, graded skin) and the single Stinger in both swarm skins
(wasp_uv.blend, work/tier_swarm_*.png) -> review/bug_view.png, review/wasp_tiers.png"""
import bpy, os, sys, runpy, subprocess
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(os.path.dirname(HERE), 'claude_shared', 'render_tier_views.py')
which = sys.argv[sys.argv.index('--') + 1]
if which == 'bug':
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'bug_anim.blend'))
    sys.argv = ['b', '--', 'Bug', os.path.join(HERE, 'review', 'bug_view.png'), '4', '0.3', '1.7',
                os.path.join(HERE, 'textures', 'bug_basecolor_graded.png')]
else:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'wasp_uv.blend'))
    sys.argv = ['b', '--', 'Wasp', os.path.join(HERE, 'review', 'wasp_tiers.png'), '4', '0.09', '0.5'] + \
        [os.path.join(HERE, 'work', f'tier_swarm_{t}.png') for t in 'bc']
runpy.run_path(TOOL, run_name='__main__')
