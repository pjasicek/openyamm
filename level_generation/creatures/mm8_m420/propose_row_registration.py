"""Propose shared batch/row alignment; review contacts before acceptance."""
import json,sys
import numpy as np
from PIL import Image
from scipy.optimize import minimize
from calibrate import body,warp
from process import ROOT,queue,save
reg=json.loads((ROOT/'registration.json').read_text());batches=json.loads((ROOT/'batches.json').read_text())
out=json.loads((ROOT/'review/row_registration_proposal.json').read_text()) if (ROOT/'review/row_registration_proposal.json').exists() else {}
for key in sys.argv[1:]:
 batch=batches[key];generated=[];targets=[];art_boxes=[];native_boxes=[]
 for n in batch['frames']:
  im=Image.new('RGBA',(576,576));im.paste(Image.open(ROOT/f'aligned_2x/{n}.png'),tuple(32+v for v in reg[n]['canvas_origin_px']));generated.append(body(im));art_boxes.append(im.getchannel('A').getbbox())
  im=Image.new('RGBA',(576,576));im.paste(queue.native(ROOT,n).resize((512,512),Image.Resampling.NEAREST),(32,32));targets.append(body(im));native_boxes.append(im.getchannel('A').getbbox())
 def objective(v):
  if not .55<v[0]<1.08 or max(abs(x) for x in v[1:])>40:return 10
  numerator=denominator=0
  for i,(a,b) in enumerate(zip(generated,targets)):
   row=i//batch['columns'];w=warp(a,[v[0],v[1]+row*v[3],v[2]+row*v[4]])
   numerator+=2*(w*b).sum();denominator+=(w*w+b*b).sum()
  return 1-numerator/max(denominator,1e-6)+.02*(v[0]-1)**2
 fits=[]
 for scale in [.65,.76,.85,1.]:
  shifts=[]
  for row in [0,1]:
   pairs=[(a,b) for i,(a,b) in enumerate(zip(art_boxes,native_boxes)) if i//batch['columns']==row]
   shifts.append(np.median([[(b[0]+b[2])/2-288-scale*((a[0]+a[2])/2-288),b[3]-288-scale*(a[3]-288)] for a,b in pairs],axis=0)/4.5)
  initial=np.array([scale,*shifts[0],*(shifts[1]-shifts[0])]);simplex=np.vstack([initial,initial+np.diag([.04,2,2,2,2])])
  fits.append(minimize(objective,initial,method='Nelder-Mead',options={'maxiter':1200,'xatol':.0005,'initial_simplex':simplex}))
 fit=min(fits,key=lambda r:r.fun);values=fit.x.tolist();out[key]={'values':values,'objective':float(fit.fun),'status':'proposal_needs_visual_review'}
 batch['accepted_calibration']=values[:3];batch['accepted_row_translation_2x_px']={'1':[round(x*4.5,3) for x in values[3:]]}
 print(key,out[key],flush=True)
save(ROOT/'review/row_registration_proposal.json',out);save(ROOT/'batches.json',batches)
