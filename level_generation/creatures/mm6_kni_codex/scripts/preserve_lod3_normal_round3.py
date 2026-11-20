"""Retain the accepted LOD3 tangent detail: this LOD has no geometry change from round 2."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
P=Path(__file__).resolve().parents[1];R=P/'review/round3'
src=P/'work/round3/high_normal.png';dst=P/'textures/round3/knight_normal_l3.png'
im=Image.open(src).convert('RGB').resize((256,256),Image.Resampling.BOX)
a=np.array(im,dtype=np.float64)/127.5-1
a/=np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-8)
Image.fromarray(np.clip((a+1)*127.5,0,255).round().astype('uint8')).save(dst,optimize=True,compress_level=9)
assert Image.open(dst).size==(256,256)
(R/'normal_lod3_selection.json').write_text(json.dumps({'method':'Accepted source tangent normal, area filtered and renormalized to 256 px. LOD3 geometry unchanged from accepted round 2.','reason':'New projected normal bake visibly shifted distant highlights; rejected (eight-view min SSIM 0.762672). Source-normal probe passes 0.972225 at native switch size.','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'final_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'rejected_bake_receipt':'normal_bake_l3.json'},indent=2)+'\n')
