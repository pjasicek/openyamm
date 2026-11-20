import runpy,bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/transfer_textures.py'),run_name='__main__')
me=bpy.data.objects['Body'].data
hits=np.load(P/'work/head_uv_hits.npy'); bad=[]
for f in me.polygons:
 if not me.attributes['head'].data[f.index].value:continue
 uv=np.array([me.uv_layers['HeadUV'].data[i].uv[:] for i in f.loop_indices]);q=uv.mean(0);x,y=np.clip((q*1024).astype(int),0,1023)
 if hits[1023-y,x]>1:bad.append({'face':f.index,'piece':me.attributes['piece'].data[f.vertices[0]].value,'center':f.center[:],'area':f.area})
(P/'work/uv_overlap_probe.json').write_text(json.dumps(bad,indent=2))
from collections import Counter
print('OVERLAP_CENTROIDS',Counter(x['piece'] for x in bad),len(bad))
