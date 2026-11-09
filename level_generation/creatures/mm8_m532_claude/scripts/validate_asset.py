from pathlib import Path
import sys,json,hashlib,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array,image_of
report={}
for filename in ('mm8_centaur.glb','mm8_centaur_bow.glb','mm8_centaur_quiver.glb'):
    path=P/'export'/filename;d,b=read_glb(path);skin=d.get('skins',[]);meshes=[]
    assert len(d['materials'])==3 and len(d['images'])==4
    for mesh in d['meshes']:
        count=0;degenerate=0
        for p in mesh['primitives']:
            at=p['attributes'];pos=accessor_array(d,b,at['POSITION']);idx=accessor_array(d,b,p['indices']).reshape(-1,3)
            assert idx.max()<len(pos)
            for key,ai in at.items():assert np.isfinite(accessor_array(d,b,ai)).all(),key
            tri=pos[idx];degenerate+=int((np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)<1e-12).sum());count+=len(idx)
            if skin:
                w=accessor_array(d,b,at['WEIGHTS_0']);j=accessor_array(d,b,at['JOINTS_0']);assert abs(w.sum(1)-1).max()<1e-4 and j.max()<72
        assert degenerate==0,(mesh['name'],degenerate)
        meshes.append({'name':mesh['name'],'triangles':count,'degenerate':degenerate})
    for a in d.get('animations',[]):
        for s in a['samplers']:
            t=accessor_array(d,b,s['input']).ravel();assert t[0]==0 and np.all(np.diff(t)>0);assert s.get('interpolation','LINEAR')in('LINEAR','STEP')
    if skin:
        assert len(skin)==1 and len(skin[0]['joints'])==72
        assert {a['name']for a in d['animations']}==set(json.loads((P/'work/clips.json').read_text()))
        for name in ('Socket_BowRelease','Socket_CastPalm','Bow','Quiver'):assert any(n.get('name')==name for n in d['nodes'])
        im,_=image_of(d,b,d['materials'][0]['pbrMetallicRoughness']['metallicRoughnessTexture']['index']);assert np.ptp(np.asarray(im)[...,0])>100
    report[filename]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'meshes':meshes,'bones':len(skin[0]['joints'])if skin else 0}
(P/'review/asset_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
