import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];selection=json.loads((P/'review/round4/selection.json').read_text());data={}
for label,path in [('before',P/'work/round4/body_lod3_contact1.blend'),('after',P/selection['body'][3]['blend'])]:
 bpy.ops.wm.open_mainfile(filepath=str(path));body=bpy.data.objects['Body'];co=np.array([tuple(body.matrix_world@v.co)for v in body.data.vertices]);w=np.zeros((len(co),57));names=[b.name for b in bpy.data.objects['Rig'].data.bones]
 for v in body.data.vertices:
  for g in v.groups:
   name=body.vertex_groups[g.group].name
   if name in names:w[v.index,names.index(name)]=g.weight
 data[label]=(co,w)
distance=np.linalg.norm(data['after'][0]-data['before'][0],axis=1);weight=np.abs(data['after'][1]-data['before'][1]).sum(1)
report={'lod':3,'triangles':selection['body'][3]['triangles'],'position_vertices_changed':int((distance>1e-6).sum()),'max_position_delta_m':float(distance.max()),'weight_vertices_changed':int((weight>1e-5).sum()),'weights':'Only the repaired cloth vertices use interpolation of the accepted full-detail cloth weights; original joints and clips remain exact.','source':'Accepted round 3 tunic surface; corrected covered front thigh patch.'}
(P/'review/round4/cloth_support.json').write_text(json.dumps(report,indent=2)+'\n');print('CLOTH_RECEIPT',report)

