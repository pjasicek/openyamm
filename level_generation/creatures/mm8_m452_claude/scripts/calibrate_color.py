"""Native GPU comparison calibration: lift only fur, preserving skin, eyes and every geometry/animation byte."""
from pathlib import Path
import sys,json,hashlib,shutil
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import accessor_bytes
base=P/'textures/rat_basecolor_graded.png';original=P/'work/rat_basecolor_before_calibration.png'
if not original.exists():shutil.copyfile(base,original)
a=np.array(Image.open(original).convert('RGB'),dtype=np.float32)
mask=np.array(Image.open(P/'textures/rat_material_classes.png').resize((2048,2048),Image.Resampling.NEAREST))==2
a[mask]*=np.array([1.25,1.30,1.22]);Image.fromarray(np.clip(a+.5,0,255).astype(np.uint8)).save(base)
model=P/'export/mm8_m452.glb';doc,old=R.read_glb(model)
before=[hashlib.sha256(accessor_bytes(doc,old,i)).hexdigest() for i in range(len(doc['accessors']))]
tex=doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index'];im=doc['textures'][tex]['source']
blob=bytearray(old);blob.extend(b'\0'*(-len(blob)%4));offset=len(blob);data=base.read_bytes();blob.extend(data)
doc['images'][im]['bufferView']=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(data)})
doc,blob=R._compact(doc,blob)
assert before==[hashlib.sha256(accessor_bytes(doc,blob,i)).hexdigest() for i in range(len(doc['accessors']))]
R.write_glb(model,doc,blob)
(P/'work/color_calibration.json').write_text(json.dumps({'reason':'Matched native fur in the New Sorpigal GPU comparison',
 'fur_srgb_gain':[1.25,1.30,1.22],'geometry_rig_uv_and_clips_unchanged':True,
 'measured_patch_median_before':[55,48,47],'native_patch_median':[69,63,57]},indent=2)+'\n')
