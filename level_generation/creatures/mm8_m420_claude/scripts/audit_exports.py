"""Audit final GLB geometry, winding, skin, clips and tier contracts before installation."""
import sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
report={}
for name in ['mm8_m420','mm8_m420_staff']:
 d,b=R.read_glb(P/'export'/f'{name}.glb')
 def acc(i):
  a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];size=np.dtype(dt).itemsize
  out=np.ndarray((a['count'],n),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*size),size));assert np.isfinite(out).all();return out
 rows=[]
 for mesh in d['meshes']:
  tri=0;deg=0;inward=0;area_sum=0;negative_area=0
  for pr in mesh['primitives']:
   pos=acc(pr['attributes']['POSITION']);ids=acc(pr['indices']).reshape(-1,3).astype(int);nrm=acc(pr['attributes']['NORMAL']);cross=np.cross(pos[ids[:,1]]-pos[ids[:,0]],pos[ids[:,2]]-pos[ids[:,0]]);area=np.linalg.norm(cross,axis=1);norm=nrm[ids].mean(1);dots=(cross*norm).sum(1)
   tri+=len(ids);deg+=int((area<1e-12).sum());bad=dots<-.1*area;inward+=int(bad.sum());area_sum+=float(area.sum());negative_area+=float(area[bad].sum())
   if 'WEIGHTS_0' in pr['attributes']:
    weights=acc(pr['attributes']['WEIGHTS_0']);assert np.abs(weights.sum(1)-1).max()<.001
    assert 'WEIGHTS_1' not in pr['attributes']
  row={'mesh':mesh['name'],'triangles':tri,'degenerate':deg,'opposed_normals':inward,'opposed_area_fraction':negative_area/max(area_sum,1e-9)};rows.append(row)
  # Reduced shadow vertices are deliberately inset and may reverse tiny triangles inside the opaque surface.
  assert deg==0,row
 report[name]={'meshes':rows,'clips':[a['name'] for a in d.get('animations',[])],'variants':d.get('extensions',{}).get('KHR_materials_variants',{}).get('variants',[])}
 print('AUDIT',name,rows)
 if name=='mm8_m420':
  assert set(report[name]['clips'])=={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget','Cast'}
  assert [v['name'] for v in report[name]['variants']]==['pirate_mage_a','pirate_mage_b','pirate_mage_c','pirate_seer_a','pirate_seer_b','pirate_seer_c']
sys.path.insert(0,str(P.parents[2]/'level_generation/decorations/mm8_3d/animated/scripts'))
from check_winding import check
for name in report:assert check(P/'export'/f'{name}.glb')==0
(P/'review/export_audit.json').write_text(json.dumps(report,indent=2)+'\n')
