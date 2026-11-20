"""Check this staged collection through the unchanged shared reviewer's localhost APIs."""
import json
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8873'


def get(path):
    with urlopen(BASE + path, timeout=30) as response:
        assert response.status == 200, path
        return response.read()


queue = json.loads(get('/api/families'))
assert queue['collection']['id'] == 'mm7-session-mm7-03'
status = json.loads((HERE/'session_status.json').read_text())
expected = {row['label']:row for row in status['families']}
assert len(queue['families']) == 8
assert sum(f['frame_count'] for f in queue['families']) == status['totals']['exported_frames']
checks = []
for family in queue['families']:
    manifest = json.loads(get('/api/family/' + family['id']))
    assert manifest['visual_acceptance'] == expected[manifest['review_label']]['accepted']
    assert manifest['quality_status'].startswith('validated_staged' if manifest['visual_acceptance'] else 'partial_')
    assert len(manifest['frames']) == family['frame_count']
    palette = next(iter(manifest['variants']))
    name = next(iter(manifest['frames']))
    page = manifest['pages'][0]
    for relative in [f'native_variants/{name}_{palette}.png', page['base'], page['mask'],
                     page['variant_previews'][palette]]:
        assert get('/media/' + family['id'] + '/' + relative).startswith(b'\x89PNG\r\n\x1a\n'), relative
    for region in manifest['review_color_regions']:
        assert get('/mask/' + family['id'] + '/0/' + region).startswith(b'\x89PNG\r\n\x1a\n'), region
    checks.append(dict(family=family['id'], frames=family['frame_count'],
                       palettes=list(manifest['variants']), accepted=manifest['visual_acceptance']))
for asset in ('/', '/app.js', '/style.css'):
    assert get(asset)
result = dict(url=BASE+'/', family_count=8, frame_count=status['totals']['exported_frames'], checks=checks,
              static_and_api_and_material_assets=True, browser_playback_inspected=False)
(HERE/'review_state/server_check.json').write_text(json.dumps(result, indent=2)+'\n')
print('Shared reviewer API and native/base/mask/palette assets verified:',len(checks),'families,',result['frame_count'],'frames.')
