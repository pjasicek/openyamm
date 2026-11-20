import bpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for label in ['body','head']:
 im=bpy.data.images.load(str(P/f'work/native_shade_{label}.exr'),check_existing=False);im.colorspace_settings.name='Non-Color';a=np.array(im.pixels[:],np.float32).reshape(1024,1024,4);np.save(P/f'work/native_shade_{label}.npy',a[::-1,:,0]);print(label,float(a[...,0].min()),float(a[...,0].max()))
