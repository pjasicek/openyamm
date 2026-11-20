"""Build standard colour/shadow LOD chains independently for body and stone rubble."""
import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path('tools').resolve()))
import build_actor_lods as lod
for node,source,out in [('Gargoyle','mm6_gar_prepared.glb','mm6_gar_body_lods.glb'),('Rubble','mm6_gar_body_lods.glb','mm6_gar_lods.glb')]:
 bpy.ops.wm.read_factory_settings(use_empty=True);lod.generate((P/'export'/source).resolve(),(P/'export'/out).resolve(),node,
  ratios=(.5,.36,.12) if node=='Gargoyle' else (.5,.18,.06))
 (P/f'export/lods_{node.lower()}.json').write_text((P/'export/lods.json').read_text())

import runpy
runpy.run_path(str(P/'scripts/preserve_lod_normals_v5.py'),run_name='__main__')
