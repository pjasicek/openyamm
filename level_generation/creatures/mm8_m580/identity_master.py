"""Focused native material reference; no gameplay or source modifications."""
from PIL import Image
from process import ROOT,queue
im=queue.native(ROOT,'m580aa2');box=im.getchannel('A').getbbox();box=(max(0,box[0]-8),max(0,box[1]-8),min(im.width,box[2]+8),min(im.height,box[3]+8));im=im.crop(box);bg=Image.new('RGBA',im.size,(255,0,255,255));bg.alpha_composite(im);bg.resize((im.width*4,im.height*4),Image.Resampling.NEAREST).convert('RGB').save(ROOT/'references/identity_material_native.png')
