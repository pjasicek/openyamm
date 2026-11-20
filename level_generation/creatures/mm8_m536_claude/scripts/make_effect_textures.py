"""Unwrap the restored Efreeti fire into a scrolling cylinder and radial fringe; measure its native flask."""
import importlib.util,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];T=P/'textures';T.mkdir(exist_ok=True)
R=P.parent/'mm7_mm8_packed_outline/session_mm8_05/mm8_m536/redo_2x/runtime_aligned_2x'
spec=importlib.util.spec_from_file_location('flame_unwrap',P.parent/'mm6_fie1_claude/scripts/make_texture.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
def load(name):return np.asarray(Image.open(R/(name+'.png')).convert('RGBA'),float)[238:492]/255
F.load=load;F.core=lambda name:np.zeros(load(name).shape[:2]);F.CAGE_FRAMES=['m536wa0','m536wb4','m536wc0','m536wd4','m536we0','m536wf4'];F.PROFILE_FRAMES=F.CAGE_FRAMES;F.FRINGE_SOURCES=[(name,side) for name in F.CAGE_FRAMES[:4] for side in [-1,1]];F.MASK_COVERAGE=.98;F.LATTICE_ALPHA_GAIN=1.
pm,a=F.cage_band();rgba=F.tile(pm,a);lum=rgba[...,:3]@np.array([.2126,.7152,.0722]);rgba[...,3]*=np.clip((lum-.06)*2.1,.32,1.)
F.save(F.bleed(rgba),T/'m536_flame.png');F.save(F.bleed(F.tile(*F.fringe(),mask=False)),T/'m536_fringe.png')
profiles=[]
for name in F.CAGE_FRAMES:
 im=load(name);top,bottom,c,r=F.silhouette(im);t=np.linspace(0,1,25);profiles.append(np.interp(t,np.linspace(0,1,len(r)),r)/138.5)
radius=np.mean(profiles,axis=0);radius[-1]=.012;radius[0]=min(.29,radius[0]);z=np.linspace(2.0,.07,25)
flask=np.asarray(Image.open(R/'m536xa0.png').convert('RGBA'),float)/255;rows=np.where((flask[...,3]>.5).sum(1)>2)[0];top,bottom=int(rows[0]),int(rows[-1]);height=(bottom-top)/138.5
# The lathe uses the bottle's measured silhouette; all surface colours come from its restored source.
centres=[];radii=[]
for y in range(top,bottom+1):
 x=np.where(flask[y,:,3]>.5)[0];centres.append((x[0]+x[-1])/2 if len(x) else 259);radii.append((x[-1]-x[0])/2 if len(x) else 1)
theta=(np.arange(512)+.5)/512*2*np.pi;yy=np.linspace(top,bottom,512);cc=np.interp(yy,np.arange(top,bottom+1),centres);rr=np.interp(yy,np.arange(top,bottom+1),radii);xx=cc[:,None]+rr[:,None]*np.sin(theta)[None,:]*.78
paint=F.sample(flask,xx,np.broadcast_to(yy[:,None],xx.shape));paint[...,3]=1;F.save(paint,T/'m536_flask.png')
rings=np.linspace(0,1,28);fr=np.interp(rings,np.linspace(0,1,len(radii)),radii)/138.5
report={'tail':{'height':z.tolist(),'radius':radius.tolist(),'tile_share':(F.BAND_END-F.BAND_START)/(1+F.OVERLAP),'fringe_inner':F.FRINGE_INNER,'fringe_outer':F.FRINGE_OUTER},'flask':{'height':height,'z':((1-rings)*height+.008).tolist(),'radius':fr.tolist(),'native_bounds':[top,bottom]},'sources':[{'path':str(R/(n+'.png')),'sha256':hashlib.sha256((R/(n+'.png')).read_bytes()).hexdigest()} for n in F.CAGE_FRAMES+['m536xa0']]}
assert .8<height<1.2 and .4<radius.max()<.7 and np.isfinite(rgba).all()
(T/'effect_profile.json').write_text(json.dumps(report,indent=2));print('EFFECTS',height,'flask height, tail radius',radius.max())
