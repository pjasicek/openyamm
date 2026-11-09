"""Assert-owned exports: geometry, UVs, winding (including glass), PBR images and resting footprint."""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from link_static_model_lods import read_glb

spec=importlib.util.spec_from_file_location('winding',ROOT/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py')
winding=importlib.util.module_from_spec(spec)
spec.loader.exec_module(winding)


def check(icon):
    path=PROJECT/f'work/vessels/{icon}_export.glb'
    doc,binary=read_glb(path)
    assert not doc.get('extensionsRequired'), (icon,'unsupported extension')
    for view in ('above','low'):
        assert (PROJECT/f'review/vessels/{icon}_{view}.png').exists()
    assert winding.check(path)==0
    points=[]
    count=0
    uv_sheet=Image.open(PROJECT/'textures/potions_basecolor.png').convert('RGB').resize((1024,512))
    draw=ImageDraw.Draw(uv_sheet)
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            pos=winding.array(doc,binary,prim['attributes']['POSITION']).astype(float)
            indices=winding.array(doc,binary,prim['indices']).reshape(-1,3)
            tex=winding.array(doc,binary,prim['attributes']['TEXCOORD_0'])
            normals=winding.array(doc,binary,prim['attributes']['NORMAL'])
            assert np.isfinite(pos).all() and np.isfinite(tex).all() and np.isfinite(normals).all()
            assert tex.min()>=-1e-6 and tex.max()<=1.000001
            assert np.allclose(np.linalg.norm(normals,axis=1),1,atol=.002)
            a,b,c=pos[indices[:,0]],pos[indices[:,1]],pos[indices[:,2]]
            areas=np.linalg.norm(np.cross(b-a,c-a),axis=1)*.5
            assert areas.min()>1e-10, (icon,'degenerate triangle',areas.min())
            # Glass is one closed exterior shell, omitted by the shared opaque-only winding audit.
            if doc['materials'][prim['material']].get('alphaMode')=='BLEND':
                volume=np.einsum('ij,ij->i',a,np.cross(b,c)).sum()/6
                assert volume>0, (icon,'inverted glass')
            points.append(pos)
            count+=len(indices)
            for triangle in indices:
                coords=tex[triangle]*[uv_sheet.width-1,uv_sheet.height-1]
                draw.line([tuple(p) for p in coords]+[tuple(coords[0])],fill=(100,180,205),width=1)
    p=np.concatenate(points)
    low,high=p.min(axis=0),p.max(axis=0)
    assert abs(low[1])<.00001, (icon,'not grounded',low)
    assert abs(high[0]+low[0])<.00001 and abs(high[2]+low[2])<.00001, (icon,'off-centre')
    assert abs(max(high[0]-low[0],high[2]-low[2])-1)<.00001
    assert high[2]-low[2]>=high[0]-low[0]-.001, (icon,'longest horizontal axis is not Blender Y')
    assert count<3200, (icon,count)
    for index,im in enumerate(doc.get('images',[])):
        view=doc['bufferViews'][im['bufferView']]
        start=view.get('byteOffset',0)
        image=Image.open(io.BytesIO(binary[start:start+view['byteLength']]))
        assert image.format=='PNG' and image.size==(2048,1024)
        if im['name']=='potions_orm':
            values=np.asarray(image)
            assert set(np.unique(values[...,2]))=={0,255}
    uv_sheet.save(PROJECT/f'review/uv/{icon}.png')
    return {'triangles':count,'meshes':len(doc['meshes']),'bounds_gltf':[low.tolist(),high.tolist()],
            'winding':'outward','uv':'finite, padded 0..1 atlas, deliberate repeated-part overlap',
            'export_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    (PROJECT/'review/uv').mkdir(exist_ok=True)
    owned=json.loads((PROJECT/'ownership.json').read_text())
    baseline=json.loads((PROJECT/'receipts/baseline.json').read_text())
    only=set(sys.argv[1:])
    report=PROJECT/'receipts/validation.json'
    results=json.loads(report.read_text()) if only else {}
    for row in owned:
        icon=row['icon']
        if icon=='7item182':
            source=ROOT/'assets_source/engine/world_items/models/item_7item182.glb'
            assert hashlib.sha256(source.read_bytes()).hexdigest()==baseline[icon]['source_sha256']
        elif not only or icon in only:
            results[icon]=check(icon)
    for icon in ('bottle30','item198','7item294'):
        doc,b=read_glb(PROJECT/f'work/vessels/{icon}_export.glb')
        assert any(m.get('alphaMode')=='BLEND' for m in doc['materials'])
    assert len(results)==41
    (PROJECT/'receipts/validation.json').write_text(json.dumps(results,indent=2)+'\n')
    print('Validated 41 replacements; assigned scroll preserved byte for byte')


if __name__=='__main__':
    main()
