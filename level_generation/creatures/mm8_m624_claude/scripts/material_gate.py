from pathlib import Path
import runpy,sys,numpy as np
from PIL import Image
sys.path.insert(0,str(Path('tools').resolve()))
P=Path(__file__).resolve().parents[1];E=P/'export';T=P/'textures';a=np.full((128,128),9,np.uint8);a[:,64:96]=8;Image.fromarray(a).save(T/'weapon_material_classes.png')
sys.argv=['prepare_actor_glb.py',str(E/'mm8_m624_lod0.glb'),str(E/'mm8_m624_runtime_lod0.glb')];runpy.run_path('tools/prepare_actor_glb.py',run_name='__main__')
sys.argv=['material_classes_to_orm.py',str(E/'mm8_m624_runtime_lod0.glb'),str(E/'mm8_m624_runtime_lod0.glb'),'--classes',str(T/'naga_body_material_classes.png'),'--head-classes',str(T/'naga_head_material_classes.png'),'--map','NagaWeapons='+str(T/'weapon_material_classes.png'),'--report',str(P/'work/material_audit.json')];runpy.run_path(str(P.parent/'claude_shared/material_classes_to_orm.py'),run_name='__main__')
