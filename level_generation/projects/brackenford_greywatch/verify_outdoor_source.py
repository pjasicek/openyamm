"""Focused native export regression: signed faces, scene bindings, entities and metadata round trip."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file
faces=[[(0,0,0),(0,512,0),(512,512,0),(512,0,0)],
       [(0,0,512),(512,0,512),(512,512,512),(0,512,512)],
       [(0,0,1024),(512,0,1280),(512,512,1280),(0,512,1024)],
       [(0,0,1536),(0,512,1536),(512,512,1792),(512,0,1792)],
       [(0,0,0),(512,0,0),(512,0,512),(0,0,512)]]
with tempfile.TemporaryDirectory(prefix='levelgen-outdoor-source-test-') as directory:
    temp=Path(directory)
    lines=[]
    for points in faces:
        lines += ['v '+' '.join(str(v) for v in p) for p in points]
    lines += ['vt 0 0','vt 1 0','vt 1 1','vt 0 1','usemtl t14c01b']
    lines += ['f '+' '.join(f'{i*4+j+1}/{j+1}' for j in range(4)) for i in range(len(faces))]
    (temp/'signed.obj').write_text('\n'.join(lines)+'\n')
    scene=json.loads((PROJECT/'source/lg01.scene.yml').read_text())
    scene['entities']=[e for e in scene['entities'] if e['name']=='Party Start']
    scene['bmodel_faces']['interactive_faces']=[{'bmodel_index':0,'face_index':4,
        'legacy_attributes':0x2000000,'cog_triggered_number':321,'cog_number':0,'cog_trigger':0}]
    terrain=json.loads((PROJECT/'source/lg01.terrain.yml').read_text())
    package=json.loads((PROJECT/'source/lg01.map.yml').read_text())
    metadata={'version':1,'map_file':'lg01.odm','bmodels':[{'geometry_id':'test:signed_faces','runtime_bmodel_index':0,
        'source':{'asset_path':str(temp/'signed.obj'),'scale':1,'preserve_source_winding':True},
        'materials':{'default_texture':'t14c01b'}}]}
    for name,data in [('lg01.map.yml',package),('lg01.scene.yml',scene),('lg01.terrain.yml',terrain),
                      ('lg01.geometry.yml',metadata)]:
        (temp/name).write_text(json.dumps(data)+'\n')
    command=[str(ROOT/'build/editor/openyamm-editor'),'--asset-root',
        '/tmp/openyamm-brackenford-greywatch/assets_editor_dev','--headless-build-map',str(temp/'lg01.map.yml')]
    result=subprocess.run(command,capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError(result.stdout+result.stderr)
    native=parse_odm_file(temp/'lg01.odm')['payload']
    actual=native['bmodels'][0]['faces']
    assert [f['polygon_type'] for f in actual]==[5,3,4,6,1]
    assert actual[4]['cog_triggered_number']==321 and actual[4]['attributes'] & 0x2000000
    assert len(native['entities'])==1 and native['entities'][0]['name'].lower()=='party start'
    saved=yaml.safe_load((temp/'lg01.geometry.yml').read_text())
    assert saved['bmodels'][0]['source']['preserve_source_winding'] is True
    assert bytes(native['height_map'])==bytes.fromhex(terrain['height_map_hex'])
    first=(temp/'lg01.odm').read_bytes()
    subprocess.run(command,check=True,capture_output=True,text=True)
    assert (temp/'lg01.odm').read_bytes()==first, 'Rebuilding the package changed the native bytes'
    report={'status':'pass','polygon_types':[5,3,4,6,1],'event_id':321,'native_party_start':True,
            'source_winding_metadata_round_trip':True,'terrain_exact':True,'rebuild_bytes_identical':True}
    (PROJECT/'review/outdoor_source_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
