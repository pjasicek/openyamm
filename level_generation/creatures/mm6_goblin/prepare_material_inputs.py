"""Derive a confidence mask for projecting only olive skin from the reviewed AI turnaround."""
from pathlib import Path
from PIL import Image,ImageFilter
import numpy as np

ROOT=Path(__file__).resolve().parent
image=Image.open(ROOT/'reference_restoration/turnaround_v1.png').convert('RGB')
pixels=np.array(image,dtype=float)
r,g,b=pixels[:,:,0],pixels[:,:,1],pixels[:,:,2]
# Suppress the gray background/iron, yellow brass and brown leather. Geometric region masks are also required.
confidence=np.clip((g/(r+1)-.92)/.10,0,1)*np.clip((.80-b/(g+1))/.16,0,1)
mask=Image.fromarray(np.uint8(confidence*255),'L').filter(ImageFilter.GaussianBlur(.65))
mask.save(ROOT/'textures/restoration_skin_confidence.png')

for name in ['hand','torso','feet']:
    image=ROOT/f'textures/{name}_surface.png'
    if image.exists():
        pixels=np.array(Image.open(image).convert('RGB'),dtype=float)
        r,g,b=pixels[:,:,0],pixels[:,:,1],pixels[:,:,2]
        confidence=np.clip((g/(r+1)-.89)/.12,0,1)*np.clip((.82-b/(g+1))/.16,0,1)
        Image.fromarray(np.uint8(confidence*255),'L').filter(ImageFilter.GaussianBlur(1)).save(
            ROOT/f'textures/{name}_surface_confidence.png')
