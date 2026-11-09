"""Check exported bridge walking surfaces and structural contact on the actual ODM."""
import hashlib
import json
import sys
from pathlib import Path

from prepare_bridges import triangle_clearance

PROJECT=Path(__file__).resolve().parent
sys.path.insert(0,str(PROJECT.parents[2]/'util'))
from map_export import parse_odm_file


def review():
    native=PROJECT/'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    payload=parse_odm_file(native)['payload']
    height=bytes(payload['height_map'])
    semantic=json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    build=json.loads((PROJECT/'review/native/build.json').read_text())
    assert hashlib.sha256(native.read_bytes()).hexdigest()==build['nativeSha256']
    models={m['id'].split('/')[-1]:m['index'] for m in semantic['bmodels']}
    assert {b['id'] for b in semantic['bridges']}=={'river_crossing','reger_crossing'}
    checks=[]
    for bridge in semantic['bridges']:
        for item in bridge['geometryChecks']:
            index=models[item['model']]
            model=payload['bmodels'][index]
            assert len(model['vertices'])>0
            digest=hashlib.sha256((PROJECT/'implementation/source/models'/(item['model']+'.obj')).read_bytes()).hexdigest()
            assert build['sourceObjSha256'][item['model']+'.obj']==digest
            spans=[]
            for face_index in item['faces']:
                face=model['faces'][face_index]
                # Explicit x/y/z avoids depending on JSON member order.
                vertices=[[model['vertices'][i][axis] for axis in ['x','y','z']] for i in face['vertex_indices']]
                for i in range(1,len(vertices)-1):
                    spans.append(triangle_clearance(height,[vertices[0],vertices[i],vertices[i+1]]))
            minimum=min(s['minimum'] for s in spans)
            maximum=max(s['maximum'] for s in spans)
            if item['kind'].startswith('buried'):
                assert maximum<=0,(bridge['id'],item,maximum)
            else:
                assert minimum>=-1e-6,(bridge['id'],item,minimum)
            checks.append({'bridge':bridge['id'],**item,'nativeBmodelIndex':index,
                           'minimumClearance':minimum,'maximumClearance':maximum})
    result={'nativeSha256':build['nativeSha256'],'checks':checks,
            'limits':'Checks actual native walking faces, beam undersides and buried pile/abutment/rail feet '
                     'against terrain triangles. Does not replace visual inspection, solid-joint review, '
                     'ordinary traversal, or movement/save-reload checks.'}
    (PROJECT/'review/native/bridge_support.json').write_text(json.dumps(result,indent=2)+'\n')
    print({'nativeBridgeContactChecks':len(checks)})


if __name__=='__main__':
    review()
