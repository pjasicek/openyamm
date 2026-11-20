"""Validate every finished minimap, source, retained layer and native export canvas."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from prepare import ROOT, HERE, HUD, sha, save
DEFAULT_HERE = HERE


def main():
    global HERE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,default=DEFAULT_HERE,help='Finished revision directory')
    args=parser.parse_args()
    HERE=args.workspace.resolve()
    exports=json.loads((HERE/'exports.json').read_text())
    scope=json.loads((HERE/'scope.json').read_text())
    assert exports['count']==exports['expected']==scope['count']==len(scope['records'])
    assert {row['target'] for row in exports['records']}=={row['target'] for row in scope['records']}
    current=json.loads((HUD/'accepted_icons.json').read_text())['records']
    targets=set();vertices=0;maximum=0;rectangular=[];inputs={}
    for row in exports['records']:
        out=HERE/row['directory'];target=row['target']
        assert target not in targets;targets.add(target)
        source=json.loads((out/'sources.json').read_text())
        capture=json.loads((out/'capture.json').read_text())
        assert sha(out/'sources.json')==row['sources_sha256']
        assert sha(out/'capture.json')==row['capture_sha256']
        assert source['scene_sha256']==sha(out/'scene.json')==capture['provenance']['scene_sha256']
        assert source['terrain_sha256']==sha(out/'terrain.png')
        assert row['recipe_sha256']==sha(HERE/'approved_recipe.json')
        assert row['noise_sha256']==sha(HERE/'approved_noise.json')
        for name,expected in source['sources'].items():
            if name not in inputs:
                inputs[name]=sha(ROOT/name)
            assert inputs[name]==expected,name
        for name,expected in source['texture_cache'].items():
            assert sha(name)==expected,name
        for name,expected in {**row['outputs'],**capture['renders']}.items():
            assert sha(out/name)==expected,name
        native=Image.open(ROOT/source['previous']['source'].replace('assets_dev/','assets_legacy/icons_20260926/',1))
        assert row['x2_size']==[n*2 for n in native.size]==current[target]['x2_size']
        with Image.open(out/'x2.png') as image:
            assert image.format=='PNG' and image.mode=='RGB' and list(image.size)==row['x2_size']
            assert min(image.getextrema()[0]) >= 0
            assert np.array(image,dtype=float).std() > 1, 'Empty output: '+target
        assert Image.open(out/'master.png').size==(2048,2048)
        alpha=np.array(Image.open(out/'objects_master.png'))[:,:,3]
        processed=np.array(Image.open(out/'objects_processed.png'))[:,:,3]
        assert np.array_equal(alpha,processed),target
        assert row['processed_object_alpha_exactly_preserved'] and row['open_water_unchanged_by_noise']
        assert not row['geometry_moved'] and capture['terrain_vertices_unchanged']
        vertices+=capture['vertex_controls'];maximum=max(maximum,capture['max_projection_error_x2_pixels'])
        if row['x2_size']!=[1024,1024]:
            rectangular.append(target)
    assert maximum < .001
    assert len(rectangular)==(7 if scope['worlds'].get('mm8') else 0)
    noise=json.loads((HERE/'approved_noise.json').read_text())
    reference_check=HERE==DEFAULT_HERE and bool(scope['worlds'].get('mm6'))
    if reference_check:
        assert sha(HERE/'maps/mm6/oute3/x2.png')==noise['reference_sha256']
    report=dict(result='PASS',count=len(targets),exports_sha256=sha(HERE/'exports.json'),
        source_files_checked=len(inputs),vertex_controls=vertices,max_projection_error_x2_pixels=maximum,
        rectangular_native_canvases_preserved=rectangular,approved_new_sorpigal_byte_identical=reference_check,
        checks=['Source, texture cache, raw render and final output hashes','Native x2 dimensions',
                'Nonempty RGB PNG exports','Unchanged object alpha','Exact geometry/camera registration',
                'Approved lighting/noise recipes and exact native map registration'],
        pilot_pixel_check='Original geometry only' if reference_check else 'New geometry revision; same approved recipe')
    save(HERE/'validation.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
