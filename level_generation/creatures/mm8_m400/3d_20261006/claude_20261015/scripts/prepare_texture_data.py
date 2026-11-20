import bpy, runpy, sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];REPO=P.parents[4]
for layer in ['UVMap','HeadUV']:
    sys.argv=['uv_raster.py','--',str(P/'master_motion.blend'),layer,'1024']
    runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
sys.argv=['head_seam_gain.py','--','--mesh','Lizardman_Body',
          '--body',str(P.parent/'textures/base_color.png'),
          '--head',str(P.parent.parent/'meshy/head_retexture_claude_20261015/texture_urls_0_base_color.png'),
          '--out',str(P/'head_seam.json')]
runpy.run_path(str(REPO/'level_generation/creatures/claude_shared/head_seam_gain.py'),run_name='__main__')
