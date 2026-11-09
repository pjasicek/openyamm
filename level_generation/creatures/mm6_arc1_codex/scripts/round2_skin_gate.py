"""Native skin mean/highlights versus shared texture albedo, with exact masks and no tier dependence."""
import json,numpy as np
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1]
def stats(rgb):
 lin=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);w=np.array([.2126,.7152,.0722]);out={}
 for label,data in [('srgb_luma',rgb@w),('linear_luminance',lin@w)]:out[label]={'mean':float(data.mean()),'p90':float(np.percentile(data,90)),'p95':float(np.percentile(data,95))}
 return out
native=np.array(Image.open(P.parent/'mm6_arc1/native/arc1sta0.png').convert('RGB'),float)/255;report={'native':'../mm6_arc1/native/arc1sta0.png','tier_policy':'skin shared, outside cloth region ramp; darker native outlines retained in the measurement','regions':{}}
for label,box,layer,file in [('face',[199,71,216,90],'HeadUV','arc1_head_basecolor_1k.png'),('forearm',[177,148,184,175],'UVMap','arc1_basecolor_1k.png')]:
 x,y,z,w=box;rgb=native[y:w,x:z];rgb=rgb[(rgb[:,:,0]>rgb[:,:,1]*1.03)&(rgb[:,:,1]>rgb[:,:,2]*1.08)&(rgb[:,:,0]>.2)]
 d=np.load(P/f'work/uvraster_{layer}.npz');mask=(d['piece']==0)&(d['pos'][:,:,2]>1.48)if label=='face'else np.isin(d['piece'],[2,3,9,10]);im=np.array(Image.open(P/'textures'/file).convert('RGB'),float)/255
 n=stats(rgb);m=stats(im[mask]);report['regions'][label]={'native_box_xyxy':box,'native_pixels':len(rgb),'model_texels':int(mask.sum()),'native':n,'model':m}
 assert all(m['srgb_luma'][k]>=n['srgb_luma'][k]for k in ['mean','p90','p95']),(label,n,m)
report['pass']=True;(P/'review/round2/skin_luminance.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
