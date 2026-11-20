"""Export harpy R8 coverage with explicit native nonlinear recolor contract."""
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(ROOT.parent/'mm6_peasants/package_family.py'),'hrp'],check=True)
p=ROOT/'manifest.json';m=json.loads(p.read_text());m['recolor_model']='masked_luminance_lut_v1'
m['recolor']={'model':'masked_luminance_lut_v1','space':'sRGB encoded RGB; R8 linear cloak coverage','operation':'i=round(255*dot(base.rgb,[.2126,.7152,.0722])); out=lerp(base.rgb,luminance_lut[i],mask.r); preserve alpha; exact base bypass','fitting':'Native-used forest-green cloak indices, usage-weighted sigma=4 luminance interpolation; materials.py','runtime':'Staged asset contract; requires LUT-aware loader/shader or deterministic variant baking before installation'}
for v in m['variants'].values():
    if 'luminance_vector' in v:v['luminance_lut']=v.pop('luminance_vector')
p.write_text(json.dumps(m,indent=2)+'\n');p=ROOT/'validation.json';v=json.loads(p.read_text());v['shipping_bytes']=(ROOT/'manifest.json').stat().st_size+sum((ROOT/page[k]).stat().st_size for page in m['pages'] for k in ['base','mask']);p.write_text(json.dumps(v,indent=2)+'\n')
