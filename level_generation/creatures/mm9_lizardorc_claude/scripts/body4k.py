import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
Image.MAX_IMAGE_PIXELS=None
U=np.load('work/uv.npz'); S=4096
im=Image.new('L',(S,S),0); d=ImageDraw.Draw(im)
for t in U['ub']: d.polygon([(float(u*S),float((1-v)*S)) for u,v in t],fill=255)
c=np.asarray(im)>0; c=ndimage.binary_dilation(c,iterations=3)
b=np.asarray(Image.open('meshy/retex_body/texture_urls_0_base_color.png').convert('RGB'))
_,(iy,ix)=ndimage.distance_transform_edt(~c,return_indices=True)
Image.fromarray(b[iy,ix]).save('textures/body4k_basecolor.png')
Image.open('textures/body_ao_2k.png').convert('L').resize((S,S),Image.BILINEAR).save('textures/body4k_ao.png'); print('ok')
