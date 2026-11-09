import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export'
sys.path.insert(0,str(Path('level_generation/creatures/claude_shared').resolve()))
sys.path.insert(0,str(Path('tools').resolve()))
import region_variants as rv
sys.argv=['shrink_shadow_lods.py',str(E/'mm8_m500_lods.glb'),str(E/'mm8_m500_shadow.glb')]
runpy.run_path(str(P/'scripts/shrink_shadow_lods.py'),run_name='__main__')
rv.apply_variants(E/'mm8_m500_shadow.glb',E/'mm8_m500.glb',P/'textures/m500_ramps.json',[('WaterElemental','openyamm_specular',1.0),('WaterElemental','openyamm_specular_mask',True),('WaterElemental','pbr.metallicFactor',0.0)])
sys.argv=['merge_head_material.py',str(E/'mm8_m500.glb'),str(E/'mm8_m500.glb')]
runpy.run_path('tools/merge_head_material.py',run_name='__main__')

# Closed skin and outward tooth surfaces use the engine's ordinary back-face culling.
from link_static_model_lods import read_glb, write_glb
for path in [E/'mm8_m500.glb',E/'mm8_m500_runtime_lod0.glb',E/'mm8_m500_lod0.glb']:
    doc,binary=read_glb(path)
    for material in doc['materials']:
        material['doubleSided']=False
        # The engine uses its scalar and MR.R mask, not Blender's KHR specular extension.
        material.get('extensions',{}).pop('KHR_materials_specular',None)
        if not material.get('extensions'):material.pop('extensions',None)
    for key in ['extensionsUsed','extensionsRequired']:
        if key in doc:doc[key]=[x for x in doc[key] if x!='KHR_materials_specular']
    write_glb(path,doc,binary)
