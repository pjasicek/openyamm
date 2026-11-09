"""Read back inert public notice faces and their fitted facade positions."""
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parents[2] / 'util'))
from map_export import parse_odm_file


def review():
    semantic = json.loads((PROJECT / 'implementation/source/mm5_sw.semantic.json').read_text())
    native = PROJECT / 'implementation/runtime/worlds/mm5/maps/mm5_sw.odm'
    payload = parse_odm_file(native)['payload']
    results = []
    for building in semantic['buildings']:
        if not building.get('publicNotice'):
            continue
        board = building['publicNotice']
        binding, = [b for b in semantic['bmodels'] if b['assembly'] == building['id']
                    and b['id'].endswith('_public_notice')]
        model = payload['bmodels'][binding['index']]
        assert all(f['attributes'] == 0 and f['cog_triggered_number'] == 0 for f in model['faces'])
        art, = [f for f in model['faces'] if f['texture_name'].lower() == board['texture']]
        with Image.open(PROJECT / 'implementation/runtime/worlds/mm5/textures' / (board['texture']+'.png')) as image:
            size = image.size
        assert (max(art['texture_us'])-min(art['texture_us']),
                max(art['texture_vs'])-min(art['texture_vs'])) == size
        local = []
        for vertex in model['vertices']:
            d = [vertex[a]-building['frontOrigin'][i] for i,a in enumerate('xy')]
            local.append((sum(d[i]*building['frontTangent'][i] for i in range(2)),
                          -sum(d[i]*building['frontOutward'][i] for i in range(2)),
                          vertex['z']-building['padHeight']))
        assert [min(v[i] for v in local) for i in range(3)] == [board['bounds'][0],board['artBounds'][1],board['bounds'][2]]
        assert [max(v[i] for v in local) for i in range(3)] == board['bounds'][3:]
        assert all(local[i][1] == board['artBounds'][1] for i in art['vertex_indices'])
        results.append({'owner':building['id'],'nativeModel':binding['index'],'texture':board['texture'],
                        'artSize':size,'newEvents':0})
    assert len(results) == 3
    output = {'nativeSha256':hashlib.sha256(native.read_bytes()).hexdigest(),'notices':results,
              'limits':'Native texture extent, fitted board envelope and inert faces. Actual wall/window contact, '
                       'readability and surrounding forecourt remain visual checks.'}
    (PROJECT / 'review/public_notices_v1/readback.json').write_text(json.dumps(output,indent=2)+'\n')
    print({'publicNotices':len(results),'nativeSha256':output['nativeSha256']})


if __name__ == '__main__':
    review()
