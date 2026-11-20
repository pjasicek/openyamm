"""Stage the inspected native map crop through the existing world presentation catalogue."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image

PROJECT = Path(__file__).resolve().parent
RUNTIME = PROJECT/'implementation/runtime/worlds/mm5'
REVIEW = PROJECT/'review/native_minimap_v1'


def stage_minimap(stage, review=REVIEW):
    read = lambda path: json.loads(path.read_text())
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    assert read(stage/'mm5-stage.json')['project']=='mm5_castleview_kalindra'
    build = read(PROJECT/'review/native/build.json')
    native = RUNTIME/'maps/mm5_sw.odm'
    rendering = read(review/'native_render.json')
    assert sha(native)==build['nativeSha256']==rendering['nativeSha256']
    world = stage/'assets_dev/worlds/mm5'
    assert sha(world/'maps/mm5_sw.odm')==sha(native)
    crop = review/'travel_crop.png'
    assert Image.open(crop).size==(1024,1024)
    catalog = read(review/'catalog.yml')
    entry, = catalog['maps']
    assert entry['map']=='mm5_sw'
    assert entry['world_bounds']=={'min_x':-24576,'max_x':24576,'min_y':-24576,'max_y':24576}
    assert not entry['reveal_entire_map']
    provenance = {'nativeSha256':sha(native), 'imageSha256':sha(crop), 'pixels':[1024,1024],
                  'worldBounds':entry['world_bounds'], 'source':'Blender bake of written ODM terrain and BModels',
                  'generator':'build_minimap_blender.py',
                  'renderEvidence':str((review/'native_render.json').relative_to(PROJECT)),
                  'limits':'Current environment checkpoint. Rebuild/review after map changes; foliage billboards omitted.'}
    for destination in [RUNTIME/'ui/maps', world/'ui/maps']:
        destination.mkdir(parents=True,exist_ok=True)
        shutil.copy2(crop,destination/'mm5_sw.png')
        shutil.copy2(review/'catalog.yml',destination/'catalog.yml')
        (destination/'mm5_sw.provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (review/'staging.json').write_text(json.dumps({**provenance,'stage':str(stage),
        'runtimeReview':'Pending in-game minimap/book alignment and exploration check'},indent=2)+'\n')
    print('Staged native travel-area minimap:',world/'ui/maps')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',type=Path,default=Path('/tmp/openyamm-mm5-castleview'))
    parser.add_argument('--review',type=Path,default=REVIEW)
    args = parser.parse_args()
    stage_minimap(args.stage.resolve(strict=True), args.review.resolve(strict=True))
