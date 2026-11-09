import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export'
sys.path.insert(0,str(Path('level_generation/creatures/claude_shared').resolve()))
import region_variants as rv
rv.apply_variants(E/'mm6_gst_lods.glb',E/'mm6_gst.glb',P/'textures/gst_ramps.json',[('Ghost','openyamm_specular',1.0),('Ghost','openyamm_specular_mask',True)])
sys.argv=['merge_head_material.py',str(E/'mm6_gst.glb'),str(E/'mm6_gst.glb')]
runpy.run_path('tools/merge_head_material.py',run_name='__main__')

# Every native Ghost frame is Lit: retain its self-lit appearance in dark rooms.
from region_variants import read_glb,write_glb
doc,binary=read_glb(E/'mm6_gst.glb')
for material in doc['materials']:material.setdefault('extensions',{})['KHR_materials_unlit']={}
used=doc.setdefault('extensionsUsed',[])
if 'KHR_materials_unlit' not in used:used.append('KHR_materials_unlit')
write_glb(E/'mm6_gst.glb',doc,binary)
