"""Restore MM7 native water motion with registered bounded AI detail and periodic residual correction."""
import importlib.util,json,shutil
import cv2
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from common import *
spec=importlib.util.spec_from_file_location('water_v2',T/'mm6_new_sorpigal_water/restoration_v2/build.py');v2=importlib.util.module_from_spec(spec);spec.loader.exec_module(v2)
spec=importlib.util.spec_from_file_location('water_v3',T/'mm6_new_sorpigal_water/restoration_v3/build.py');v3=importlib.util.module_from_spec(spec);spec.loader.exec_module(v3)

def main():
 atlas=Image.open(P/'water/restored_atlas_raw.png').convert('RGB');original=[];frames=[];deltas=[]
 yy,xx=np.mgrid[:256,:256].astype('float32')
 for i in range(14):
  native=read(P/'references'/f'7hdwtr{i:03}.png',256);original.append(native)
  x,y=i%4,i//4
  ai=np.asarray(atlas.crop((round(x*atlas.width/4),round(y*atlas.height/4),round((x+1)*atlas.width/4),round((y+1)*atlas.height/4))).resize((256,256),Image.Resampling.LANCZOS),float)
  flow=cv2.calcOpticalFlowFarneback(cv2.cvtColor(seams.byte(native),cv2.COLOR_RGB2GRAY),cv2.cvtColor(seams.byte(ai),cv2.COLOR_RGB2GRAY),None,.5,3,21,5,7,1.5,0)
  ai=cv2.remap(ai.astype('float32'),xx+flow[:,:,0],yy+flow[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)
  delta=ai-native;delta-=gaussian_filter(delta,(3,3,0),mode='wrap');deltas.append(v2.periodic_residual(np.clip(delta*.5,-12,12)))
 for i,native in enumerate(original):
  neighbors=[]
  for j in ((i-1)%14,(i+1)%14):
   a=cv2.cvtColor(seams.byte(native),cv2.COLOR_RGB2GRAY);b=cv2.cvtColor(seams.byte(original[j]),cv2.COLOR_RGB2GRAY)
   flow=cv2.calcOpticalFlowFarneback(np.tile(a,(3,3)),np.tile(b,(3,3)),None,.5,3,21,5,7,1.5,0)[256:512,256:512]
   neighbors.append(cv2.remap(deltas[j].astype('float32'),xx+flow[:,:,0],yy+flow[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP))
  frames.append(seams.byte(v2.periodic_residual(native+.5*deltas[i]+.25*neighbors[0]+.25*neighbors[1])))
 before=np.asarray(frames)
 v3.P=P/'water'
 repaired=v3.repair(before.astype(float))
 distance=np.minimum.reduce([xx,yy,255-xx,255-yy]);weight=np.clip((24-distance)/8,0,1)[:,:,None]
 frames=[]
 for i,frame in enumerate(repaired):
  neighbors=[]
  for j in ((i-1)%14,(i+1)%14):
   a=cv2.cvtColor(seams.byte(frame),cv2.COLOR_RGB2GRAY);b=cv2.cvtColor(seams.byte(repaired[j]),cv2.COLOR_RGB2GRAY)
   flow=cv2.calcOpticalFlowFarneback(np.tile(a,(3,3)),np.tile(b,(3,3)),None,.5,3,21,5,7,1.5,0)[256:512,256:512]
   neighbors.append(cv2.remap(repaired[j].astype('float32'),xx+flow[:,:,0],yy+flow[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP))
  frames.append(seams.byte(frame+weight*(.25*neighbors[0]+.25*neighbors[1]-.5*frame)))
 assert np.array_equal(np.asarray(frames)[:,24:-24,24:-24],before[:,24:-24,24:-24])
 checks=[]
 for i,a in enumerate(frames):
  save(OUT/f'7hdwtr{i:03}.png',a)
  checks.append(dict(frame=i,mean_rgb_shift=(a.mean((0,1))-original[i].mean((0,1))).tolist(),broad_correlation=float(np.corrcoef(gaussian_filter(a.astype(float),(3,3,0)).ravel(),gaussian_filter(original[i],(3,3,0)).ravel())[0,1]),seams=v3.local_seams([a])))
 shutil.copy2(OUT/'7hdwtr000.png',OUT/'7wtrtyl.png')
 for name,ims in [('native',original),('restored',frames)]:
  views=[Image.fromarray(np.tile(seams.byte(a),(3,3,1))) for a in ims]
  views[0].save(P/'water'/f'{name}_repeat.png')
  views[0].save(P/'water'/f'{name}_loop.webp',save_all=True,append_images=views[1:],duration=117,loop=0,lossless=True)
 steps=lambda f:[float(abs(f[(i+1)%14].astype(float)-f[i]).mean()) for i in range(14)]
 report=dict(frame_ticks=15,ticks_per_second=128,runtime_size=256,note='Hardware source frames are already256; matches land terrain-array resolution. Water fallback native128 becomes256.',source_materials_sha256=sha(ROOT/'assets_dev/engine/rendering/surface_materials.yml'),checks=checks,native_steps=steps(original),restored_steps=steps(frames),local_seams=v3.local_seams(frames))
 (P/'water/report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['local_seams']))
if __name__=='__main__':main()
