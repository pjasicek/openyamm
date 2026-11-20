"""Isolate the selected LOD2's single folded chart face; retain geometry and reproject its textures from LOD0."""
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
from PIL import Image,ImageDraw

P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path[:0]=[str(R/'tools'),str(P/'scripts')]
from merge_head_material import read_glb,accessor_array
from check_geometry_uv import intersections
H=R/'level_generation/creatures/lod_repair_claude/scripts'
work=P/'work/lod_repair/work/ion_cannon'
result=json.loads((work/'result.json').read_text());step=result['chosen']
built=work/f'{step}.built.glb';bake=work/f'bake_{step}'
path=bake/'lod2.npz'
if not (bake/'lod2_before_chart_fix.npz').exists():(bake/'lod2_before_chart_fix.npz').write_bytes(path.read_bytes())
raw=np.load(bake/'lod2_before_chart_fix.npz');arrays={k:raw[k] for k in raw.files}
uv=arrays['p7_uv'].astype(float);size=int(arrays['p7_size'])
assert intersections(uv)==[(57,2436),(59,2436),(1478,2436)]
doc,binary=read_glb(built);primitive=doc['meshes'][doc['meshes'][0]['extras']['openyamm_lods'][1]]['primitives'][7]
ids=accessor_array(doc,binary,primitive['indices']).reshape(-1,3)
co=accessor_array(doc,binary,primitive['attributes']['POSITION'])[ids].astype(float)
area3=np.linalg.norm(np.cross(co[:,1]-co[:,0],co[:,2]-co[:,0]),axis=1)/2
e1,e2=uv[:,1]-uv[:,0],uv[:,2]-uv[:,0];area2=abs(e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0])/2
factor=np.sqrt(area2.sum()/area3.sum())
triangle=co[2436];u=triangle[1]-triangle[0];u/=np.linalg.norm(u)
n=np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0]);n/=np.linalg.norm(n);v=np.cross(n,u)
new=np.column_stack(((triangle-triangle[0])@u,(triangle-triangle[0])@v))*factor
new-=new.min(0)
# Reserve a narrow atlas band; the existing four-pixel chart gutters leave no 20x19-pixel free pocket.
pack_scale=1-(np.ceil(np.ptp(new,axis=0)[1]*size)+11)/size
uv*=pack_scale;new*=pack_scale
# Reserve a whole empty rectangle around the new chart, including four-pixel filtering margins.
mask=Image.new('L',(size,size),0);draw=ImageDraw.Draw(mask)
for i,face in enumerate(uv):
    if i!=2436:draw.polygon([tuple(p*size) for p in face],fill=1)
occupied=np.asarray(mask,dtype=int);pad=4
width,height=np.ceil(np.ptp(new,axis=0)*size).astype(int)+2*pad+2
summed=np.pad(occupied,((1,0),(1,0))).cumsum(0).cumsum(1)
counts=summed[height:,width:]-summed[:-height,width:]-summed[height:,:-width]+summed[:-height,:-width]
yx=np.argwhere(counts==0);assert len(yx),(width,height)
y,x=map(int,yx[0]);new+=(np.array([x,y])+pad+.5)/size
uv[2436]=new;assert not intersections(uv)
arrays['p7_uv']=uv.astype(np.float32);np.savez(path,**arrays)
py=os.environ['LOD_REPAIR_PYTHON']
subprocess.run([py,'-B',str(H/'transfer_textures.py'),str(built),'IonCannon',str(bake),'2'],check=True)
fixed=work/f'{step}_uv_fixed.glb'
subprocess.run([py,'-B',str(H/'apply_bake.py'),str(built),'IonCannon',str(bake),str(fixed),'2,3'],check=True)
(P/'work/lod_repair/export/ion_cannon.glb').write_bytes(fixed.read_bytes())
report={'lod':2,'primitive':7,'face':2436,'previous_overlaps':3,'new_overlaps':0,
        'padding_pixels':pad,'existing_chart_uniform_scale':float(pack_scale),'atlas_size':size,'new_chart_bounds':new.tolist(),
        'geometry_changed':False,'method':'Planar face chart at the atlas mean surface density in an empty padded rectangle; shared LOD0 reprojection.'}
(P/'review/lod_uv_repair.json').write_text(json.dumps(report,indent=2)+'\n')
print('LOD2 folded face repaired and maps reprojected; geometry unchanged.')
