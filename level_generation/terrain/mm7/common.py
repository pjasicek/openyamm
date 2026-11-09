"""Shared MM7 restoration paths and the reviewed material/gutter implementation."""
import hashlib, importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parent
T=P.parent
ROOT=P.parents[2]
spec=importlib.util.spec_from_file_location('terrain_seams',T/'seam_repair/build.py')
seams=importlib.util.module_from_spec(spec);spec.loader.exec_module(seams)
OUT=P/'runtime_x2/worlds/mm7/terrain_x2'
M=P/'masters/v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p,size=None):
 im=Image.open(p).convert('RGB')
 if size:im=im.resize((size,size),Image.Resampling.LANCZOS)
 return np.asarray(im,float)
def up(a):return np.asarray(Image.fromarray(a.astype('float32')).resize((512,512),Image.Resampling.BICUBIC),float)
def save(p,a):p.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(seams.byte(a)).save(p)
def tone(a,target):
 # Match global channel moments, without importing native pixels or broad tile stamps.
 return np.clip((a-a.mean((0,1)))*np.clip(target.std((0,1))/np.maximum(a.std((0,1)),1),.65,1.35)+target.mean((0,1)),0,255)
