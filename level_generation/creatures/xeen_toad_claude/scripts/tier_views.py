"""Tier preview: claude_shared/render_tier_views.py on work/anim_v1.blend with the baked tier previews of
claude_shared/tier_textures.py (work/tier_toad_*.png) -> review/tiers_abc.png"""
import bpy, os, sys, runpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
sys.argv = ['blender', '--', 'Toad', os.path.join(HERE, 'review', 'tiers_abc.png'), '4', '0.4', '2.3'] + \
    [os.path.join(HERE, 'work', f'tier_toad_{t}.png') for t in 'abc']
runpy.run_path(os.path.join(os.path.dirname(HERE), 'claude_shared', 'render_tier_views.py'), run_name='__main__')
