from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for name in ['transfer_textures','repair_head_uv','bake_ao']:
 runpy.run_path(str(p/'scripts'/f'{name}.py'),run_name='__main__')
