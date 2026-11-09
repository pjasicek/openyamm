"""Check actual state/LOD payloads, glow sequencing, loader contracts and local viewer dependencies."""
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
from PIL import Image

P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path[:0]=[str(R/'tools'),str(P/'scripts')]
from merge_head_material import read_glb,accessor_array
from build_actor_lods import accessor_bytes
from check_geometry_uv import intersections


def image_hashes(d,b):
    return [hashlib.sha256(b[(v:=d['bufferViews'][im['bufferView']]).get('byteOffset',0):
                              v.get('byteOffset',0)+v['byteLength']]).hexdigest() for im in d['images']]


def check():
    config=json.loads((P/'charging_states.json').read_text())
    neutral,nb=read_glb(P/'work/ion_cannon_zones.glb')
    ready,rb=read_glb(P/'work/ion_cannon_ready.glb')
    body=ready['meshes'][0]
    for before,after in zip(neutral['meshes'],body['primitives']):
        before=before['primitives'][0]
        for semantic,index in before['attributes'].items():
            assert accessor_bytes(neutral,nb,index)==accessor_bytes(ready,rb,after['attributes'][semantic]),semantic
        assert accessor_bytes(neutral,nb,before['indices'])==accessor_bytes(ready,rb,after['indices'])
    assert len(body['primitives'])==8
    levels=[0]+body['extras']['openyamm_lods']
    counts=[sum(ready['accessors'][p['indices']]['count']//3 for p in ready['meshes'][i]['primitives']) for i in levels]
    assert counts[0]==7916 and all(a>b for a,b in zip(counts,counts[1:]))
    uv_checks=[]
    for level,index in enumerate(levels):
        mesh=ready['meshes'][index]
        assert {ready['materials'][p['material']]['name'] for p in mesh['primitives']}>=set('GC_'+z for z in config['zones'])
        for p in mesh['primitives']:
            a=p['attributes'];ids=accessor_array(ready,rb,p['indices']).reshape(-1,3)
            co=accessor_array(ready,rb,a['POSITION'])[ids]
            assert np.linalg.norm(np.cross(co[:,1]-co[:,0],co[:,2]-co[:,0]),axis=1).min()>1e-10
            if 'baseColorTexture' not in ready['materials'][p['material']].get('pbrMetallicRoughness',{}):continue
            uv=accessor_array(ready,rb,a['TEXCOORD_0'])[ids].astype(float)
            assert np.isfinite(uv).all() and uv.min()>=0 and uv.max()<=1
            e1,e2=uv[:,1]-uv[:,0],uv[:,2]-uv[:,0]
            assert abs(e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0]).min()>1e-14
            overlaps=intersections(uv);assert not overlaps,(level,overlaps[:10])
            uv_checks.append({'level':level,'textured_triangles':len(ids),'overlap_pairs':0})
    exports={}
    for state,spec in config['states'].items():
        path=P/'export'/spec['file'];d,b=read_glb(path)
        assert b==rb and d['meshes']==ready['meshes'] and d['accessors']==ready['accessors']
        assert not d.get('skins') and not d.get('animations')
        position_accessors=set()
        for i,mesh in enumerate(d['meshes']):
            for key,limit in [('openyamm_lods',3),('openyamm_shadow_lods',4)]:
                chain=mesh.get('extras',{}).get(key)
                if chain is not None:assert 0<len(chain)<=limit and len(set(chain))==len(chain) and all(0<=j<len(d['meshes']) and j!=i for j in chain),(i,key)
            for p in mesh['primitives']:
                index=p['attributes']['POSITION'];a=d['accessors'][index]
                positions=accessor_array(d,b,index)
                assert len(positions)>0 and np.isfinite(positions).all(),(path.name,i,index)
                assert a.get('min')==positions.min(axis=0).tolist(),(path.name,i,index,'POSITION min')
                assert a.get('max')==positions.max(axis=0).tolist(),(path.name,i,index,'POSITION max')
                position_accessors.add(index)
                n=accessor_array(d,b,p['attributes']['NORMAL'])
                assert np.isfinite(n).all() and np.max(abs(np.linalg.norm(n,axis=1)-1))<1e-3
        strengths={}
        for m in d['materials']:
            pbr=m.get('pbrMetallicRoughness',{});extra=m.get('extras',{})
            assert not extra.get('openyamm_specular_mask') or 'metallicRoughnessTexture' in pbr,m['name']
            assert 'emissiveTexture' not in m
            assert 0<=m.get('extensions',{}).get('KHR_materials_emissive_strength',{}).get('emissiveStrength',1)<=16
            if m['name'].startswith('GC_'):
                z=m['name'][3:];level='dark' if state=='dark' else 'hot' if state=='c5' and z=='muzzle' else 'lit' if z in spec['lit'] else 'dim'
                assert m['emissiveFactor']==config['levels'][level]['factor']
                strength=m['extensions']['KHR_materials_emissive_strength']['emissiveStrength']
                assert strength==config['levels'][level]['strength']
                assert 'baseColorTexture' not in pbr and not extra.get('openyamm_specular_mask')
                strengths[z]=strength
            else:assert not any(m.get('emissiveFactor',[]))
        arc=next(n for n in d['nodes'] if n.get('name')=='GC_Arcs')
        assert ('mesh' in arc)==(state=='c5')
        assert image_hashes(d,b)==image_hashes(ready,rb)
        winding=subprocess.run([sys.executable,'-B',str(R/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'),str(path)],check=True,text=True,capture_output=True)
        exports[state]={'file':str(path.relative_to(P)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'bytes':path.stat().st_size,'body_lod_triangles':counts,'emission_strengths':strengths,
                        'position_accessors_with_verified_bounds':len(position_accessors),
                        'arcs_visible':state=='c5','winding':winding.stdout.strip()}
    sizes=[]
    for im in ready['images']:
        v=ready['bufferViews'][im['bufferView']];offset=v.get('byteOffset',0)
        with Image.open(io.BytesIO(rb[offset:offset+v['byteLength']])) as image:sizes.append(list(image.size))
    viewer=P/'review/viewer';manifest=json.loads((viewer/'manifest.json').read_text())
    assert [m['id'] for m in manifest['models']]==list(config['states'])
    for m in manifest['models']:
        f=viewer/m['url'].split('?')[0];assert hashlib.sha256(f.read_bytes()).hexdigest()==m['sha256']
        d,b=read_glb(f);assert d['animations'][0]['name']=='Standing'
        assert d['animations'][0]['channels'][0]['target']['node']==len(d['nodes'])-1
        assert d['meshes']==ready['meshes']
        assert d['accessors'][:len(ready['accessors'])]==ready['accessors']
    for a in manifest['clips']['Standing']['anchors']:
        for image in a['source_images']:assert (viewer/image).resolve().is_file(),image
    html=(viewer/'index.html').read_text()
    imports=json.loads(re.search(r'<script type="importmap">(.*?)</script>',html).group(1))['imports']
    assert (viewer/imports['three']).resolve().is_file()
    for module in ['loaders/GLTFLoader.js','controls/OrbitControls.js']:
        assert (viewer/imports['three/addons/']/module).resolve().is_file()
    subprocess.run(['node','--check',str(viewer/'review.js')],check=True)
    assert json.loads((viewer/'feedback/user_feedback.json').read_text())['findings']==[]
    report={'status':'PASS','lod0_geometry_normals_uvs':'Byte-identical to the checked zone master',
        'body_lod_triangles':counts,'textured_uvs':uv_checks,'texture_image_sizes':sizes,
        'state_payloads':'All seven share identical geometry and image bytes; c5 alone draws the arc node.',
        'exports':exports,'viewer':'Seven choices, static hold clip, matching hashes, five references, dependencies and JS checked; no browser opened.',
        'limits':'Static loader-contract checks, not native execution. Viewer acceptance is recorded in progress; native execution and Crown binding remain integrator-owned.'}
    (P/'review/final_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: seven states, LODs',counts,', POSITION bounds, UVs, winding, source retention, loader contracts and viewer files.')


if __name__=='__main__':check()
