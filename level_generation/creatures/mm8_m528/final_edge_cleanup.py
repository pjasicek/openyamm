"""Remove demonstrated green compensation fringe; preserve alpha and native blue/gold/brown."""
import json,numpy as np
from scipy import ndimage as ndi
from PIL import Image
from process import ROOT,save
report=[]
for folder in ['final_cleaned','aligned_2x']:
 for p in sorted((ROOT/folder).glob('*.png')):
  im=Image.open(p).convert('RGBA');a=np.array(im);alpha=a[:,:,3].copy();c=a[:,:,:3];band=(alpha>0)&((ndi.distance_transform_edt(alpha>=250)<=4)|(alpha<255));select=band&(c[:,:,1]>np.maximum(c[:,:,0],c[:,:,2]));c[:,:,1][select]=np.maximum(c[:,:,0],c[:,:,2])[select];assert np.array_equal(alpha,a[:,:,3]);Image.fromarray(a).save(p);report.append({'path':str(p.relative_to(ROOT)),'changed_pixels':int(select.sum())})
save(ROOT/'review/final_edge_cleanup.json',{'method':'On four-pixel alpha contour and every partially transparent pixel, cap green at max(red,blue). No intended green exists in native palette 528 Wisp art. Demonstrated on smoke outlines and final dying sparks; preserve alpha, native cool-blue sparks, pale gold-white and orange/brown hot cores.','frames':report,'alpha_unchanged':True})
print('Removed compensation green from',sum(r['changed_pixels'] for r in report),'pixels; alpha unchanged.')
