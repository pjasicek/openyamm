"""Validate the neutral upload against the zone master and exact packed UV triangles; no renderer/network."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from merge_head_material import read_glb, accessor_array

ZONES = ['Opaque','GC_breech','GC_pods','GC_ring1','GC_ring2','GC_ring3','GC_ring4','GC_muzzle']
EPS = 1e-8


def intersections(uv):
    edges = np.roll(uv,-1,axis=1)-uv
    axes = np.stack((-edges[:,:,1],edges[:,:,0]),axis=-1)
    axes /= np.linalg.norm(axes,axis=-1)[:,:,None]
    lo,hi = uv.min(1),uv.max(1)
    pairs = []
    for i,a in enumerate(uv):
        candidates = np.flatnonzero(np.all(hi>lo[i]+EPS,axis=1)&np.all(lo<hi[i]-EPS,axis=1))
        candidates = candidates[candidates>i]
        if not len(candidates):continue
        direction = np.concatenate((np.broadcast_to(axes[i],(len(candidates),3,2)),axes[candidates]),axis=1)
        ap = np.einsum('v d,n a d->n a v',a,direction)
        bp = np.einsum('n v d,n a d->n a v',uv[candidates],direction)
        overlap = np.all((ap.max(-1)>bp.min(-1)+EPS)&(bp.max(-1)>ap.min(-1)+EPS),axis=-1)
        pairs.extend((i,int(j)) for j in candidates[overlap])
    return pairs


def islands_and_gutter(uv):
    parent = list(range(len(uv)))
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    edges = defaultdict(list)
    for i,tri in enumerate(uv):
        keys = [tuple(v) for v in np.round(tri,7)]
        for j in range(3):
            edges[tuple(sorted((keys[j],keys[(j+1)%3])))].append(i)
    for faces in edges.values():
        for f in faces[1:]:parent[find(f)]=find(faces[0])
    island = np.array([find(i) for i in range(len(uv))])
    boundary = [(edge,int(island[faces[0]])) for edge,faces in edges.items() if len(faces)==1]
    segments = np.array([x[0] for x in boundary]);groups=np.array([x[1] for x in boundary])
    lo,hi=segments.min(1),segments.max(1)
    best=.01
    def point_segment(p,a,b):
        delta=b-a
        t=np.clip(np.einsum('ij,ij->i',p-a,delta)/np.einsum('ij,ij->i',delta,delta),0,1)
        return np.linalg.norm(p-(a+t[:,None]*delta),axis=1)
    for i,(a,b) in enumerate(segments):
        ids=np.flatnonzero((groups!=groups[i])&np.all(lo<hi[i]+best,axis=1)&np.all(hi>lo[i]-best,axis=1))
        ids=ids[ids>i]
        if not len(ids):continue
        c,d=segments[ids,0],segments[ids,1]
        aa=np.broadcast_to(a,c.shape);bb=np.broadcast_to(b,c.shape)
        distance=np.minimum.reduce((point_segment(aa,c,d),point_segment(bb,c,d),
                                    point_segment(c,aa,bb),point_segment(d,aa,bb)))
        best=min(best,float(distance.min()))
    return island,best


def fingerprint(pos,uv):
    values=np.concatenate((np.rint(pos.astype(np.float64)*1e5),np.rint(uv.astype(np.float64)*1e6)),axis=-1).astype(np.int64)
    return Counter(tuple(sorted(tuple(v) for v in tri)) for tri in values)


def glb(path):
    doc,binary=read_glb(path)
    assert not any(doc.get(k) for k in ('animations','skins','images','textures')),path
    positions,uvs,counts=[],[],{}
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            a=prim['attributes'];assert set(a)=={'POSITION','NORMAL','TEXCOORD_0'},a
            index=accessor_array(doc,binary,prim['indices']).reshape(-1,3)
            pos=accessor_array(doc,binary,a['POSITION'])
            uv=accessor_array(doc,binary,a['TEXCOORD_0'])
            normal=accessor_array(doc,binary,a['NORMAL'])
            assert np.isfinite(normal).all() and np.max(abs(np.linalg.norm(normal,axis=1)-1))<1e-4
            positions.append(pos[index]);uvs.append(uv[index])
            material=doc['materials'][prim['material']]
            assert not material.get('doubleSided',False),material
            counts[material['name']]=len(index)
    return doc,np.concatenate(positions),np.concatenate(uvs),counts


def main():
    a=np.array([[0.,0.],[1.,0.],[0.,1.]])
    assert intersections(np.array([a,a+.1]))==[(0,1)]
    assert not intersections(np.array([a,np.array([[1.,0.],[1.,1.],[0.,1.]])]))
    assert not intersections(np.array([a,a+2]))
    raw=np.load(P/'work/ion_cannon_uv_triangles.npz')
    co,uv,zones=raw['positions'],raw['uv'],raw['zones']
    assert len(co)==7916 and np.isfinite(co).all() and np.isfinite(uv).all()
    area3=np.linalg.norm(np.cross(co[:,1]-co[:,0],co[:,2]-co[:,0]),axis=1)/2
    e1,e2=uv[:,1]-uv[:,0],uv[:,2]-uv[:,0]
    area2=abs(e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0])/2
    assert area3.min()>1e-10 and area2.min()>1e-14,(area3.min(),area2.min())
    assert uv.min()>=-EPS and uv.max()<=1+EPS
    overlaps=intersections(uv)
    assert not overlaps,('UV interior overlaps',overlaps[:10],len(overlaps))
    island,gutter=islands_and_gutter(uv)
    assert gutter*2048>=8-.01,('UV gutter',gutter*2048)
    density=[float(np.sqrt(area2[island==i].sum()/area3[island==i].sum())*2048) for i in set(island)]
    expected=co[:,:,[0,2,1]].copy();expected[:,:,2]*=-1
    # glTF export flips V in float32; do the same before quantized comparison.
    uv_gltf=uv.astype(np.float32);uv_gltf[:,:,1]=1-uv_gltf[:,:,1]
    expected_fingerprint=fingerprint(expected,uv_gltf)
    results={}
    for stem in ('ion_cannon_neutral_upload','ion_cannon_zones'):
        path=P/'work'/f'{stem}.glb'
        doc,pos,uv_export,counts=glb(path)
        assert fingerprint(pos,uv_export)==expected_fingerprint,(stem,'Export geometry/UV mismatch')
        if stem.endswith('zones'):
            assert set(counts)==set(ZONES),counts
            assert counts=={name:int((zones==i).sum()) for i,name in enumerate(ZONES)}
        else:
            assert len(doc['meshes'])==len(doc['materials'])==len(doc['nodes'])==1
            assert counts=={'IonCannon_Neutral':len(co)}
        winding=subprocess.run([sys.executable,str(ROOT/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'),str(path)],text=True,capture_output=True,check=True)
        results[stem]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,
                       'triangles':len(co),'material_triangles':counts,'winding':winding.stdout.strip(),
                       'bounds_gltf_metres':{'min':pos.min((0,1)).tolist(),'max':pos.max((0,1)).tolist()},
                       'position_uv_roundtrip':'matches editable master, position 1e-5 m / UV 1e-6'}
    report={'status':'PASS','exports':results,'uv':{'atlas_resolution':2048,'islands':len(set(island)),
        'interior_overlap_pairs':0,'overlap_method':'Continuous triangle SAT, 1e-8 UV tolerance; boundary touching allowed',
        'minimum_island_gutter_pixels':gutter*2048,'uv_area_coverage':float(area2.sum()),
        'minimum_triangle_uv_area':float(area2.min()),'minimum_triangle_world_area_m2':float(area3.min()),
        'island_texels_per_metre_min_median_max':[min(density),float(np.median(density)),max(density)],
        'bounds':[float(uv.min()),float(uv.max())]},
        'scope':'Local neutral upload only; final textures, far LODs, browser/native review and staging pending'}
    (P/'review/geometry/geometry_uv_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    sheet=Image.new('RGB',(2048,2048),(20,22,26));draw=ImageDraw.Draw(sheet)
    colors=[(170,173,180),(220,60,170),(55,180,220),(220,80,50),(220,175,30),(90,195,45),(60,110,220),(235,210,225)]
    for tri,zone in zip(uv,zones):
        xy=np.column_stack((tri[:,0]*2048,(1-tri[:,1])*2048))
        draw.polygon([tuple(v) for v in xy],fill=colors[int(zone)],outline=(35,35,40))
    sheet.save(P/'review/geometry/uv_layout.png')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
