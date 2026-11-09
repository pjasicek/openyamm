"""Package single-palette native actor."""
import subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(ROOT.parent/'mm6_peasants/package_family.py'),'hyd'],check=True)
p=ROOT/'manifest.json';m=json.loads(p.read_text())
m['recolor_model']='masked_native_rgb_displacement_lut_v1'
m['recolor']={'model':m['recolor_model'],'space':'sRGB encoded RGB, linear R8 coverage','operation':'Trilinear sample 33x33x33 native RGB displacement LUT with base RGB, add mask*delta; clamp RGB; preserve alpha; exact base bypass.','fitting':'Eight nearest used native palette colors, smooth Gaussian RGB-distance weighting, target chroma with enhanced/native luminance ratio; materials.py','runtime':'Requires RGB LUT sampling in loader/shader; offline previews implemented, staged only.'}
for variant in m['variants'].values():
 if 'luminance_vector' in variant:variant['rgb_displacement_lut']=variant.pop('luminance_vector')
m['memory_bytes']['variant_rgb_luts_float32']=2*33**3*3*4
p.write_text(json.dumps(m,indent=2)+'\n')
