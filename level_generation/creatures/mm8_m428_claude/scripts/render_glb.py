"""Driver: claude_shared/render_glb_views.py on export/mm8_m428.glb (rest pose, tier A base colour)."""
import runpy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.argv = ['render_glb_views.py', '--', str(P / 'export/mm8_m428.glb'), str(P / 'review/glb_rest'), '-y', '900']
runpy.run_path(str(P.parent / 'claude_shared/render_glb_views.py'), run_name='__main__')
