import sys,json,numpy as np
from pathlib import Path
from PIL import Image
from scipy.ndimage import distance_transform_edt,binary_erosion
folder=Path(sys.argv[1]);report=[]
for i in range(int(sys.argv[2])):
 uv=np.asarray(Image.open(folder/f'{i}_uv_coverage.png').convert('L'))>127;hit=np.asarray(Image.open(folder/f'{i}_coverage.png').convert('L'))>127;interior=binary_erosion(uv,iterations=1);miss=interior&~hit
 row={'material':i,'uv_pixels':int(uv.sum()),'projected_pixels':int((uv&hit).sum()),'missed_interior_pixels':int(miss.sum())};report.append(row)
 if uv.any():
  assert not miss.any(),row
  valid=uv&hit;indices=distance_transform_edt(~valid,return_distances=False,return_indices=True)
  for key in ['basecolor','region_mask','metal_rough','normal','material_classes']:
   p=folder/f'{i}_{key}.png';a=np.asarray(Image.open(p));Image.fromarray(a[tuple(indices)]).save(p)
(folder/'projection_coverage.json').write_text(json.dumps(report,indent=2));print('PROJECTION COVERAGE',report,flush=True)
