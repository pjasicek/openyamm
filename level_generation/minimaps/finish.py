"""Export the approved light-noise treatment from the registered terrain/object renders."""
import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
DEFAULT_HERE = HERE
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from prepare import sha, save
from processing import grade, random_pick, composite, rgba, openraster


def finish(entry):
    out = HERE/entry['directory']
    recipe = json.loads((HERE/'approved_recipe.json').read_text())
    noise = json.loads((HERE/'approved_noise.json').read_text())
    capture = json.loads((out/'capture.json').read_text())
    sources = json.loads((out/'sources.json').read_text())
    assert capture['provenance']['recipe_sha256'] == sha(HERE/'approved_recipe.json')
    assert capture['max_projection_error_x2_pixels'] < .001
    assert all(sha(out/name) == expected for name,expected in capture['renders'].items())
    assert all(sha(ROOT/path) == expected for path,expected in sources['sources'].items())
    terrain = np.array(Image.open(out/'terrain_master.png').convert('RGBA'),dtype=np.float32)/255
    objects = np.array(Image.open(out/'objects_master.png').convert('RGBA'),dtype=np.float32)/255
    assert terrain.shape == objects.shape == (2048,2048,4)
    levels = recipe['object_levels']
    corrected = objects.copy()
    corrected[:,:,:3] = np.clip((objects[:,:,:3]-levels['black'])/(levels['white']-levels['black']),0,1)**(1/levels['gamma'])
    corrected = grade(corrected,recipe)
    assert np.array_equal(corrected[:,:,3],objects[:,:,3])
    picked = grade(random_pick(terrain,recipe['terrain_random_pick']),recipe)
    picked[:,:,3] = 1
    # The accepted trial applied noise to saved 8-bit processed layers. Keep that exact stage boundary.
    terrain = np.array(rgba(picked),dtype=np.float32)/255
    corrected = np.array(rgba(corrected),dtype=np.float32)/255
    atlas = np.array(Image.open(out/'terrain.png').convert('RGB'),dtype=np.float32)
    water = (atlas[:,:,2]>atlas[:,:,0]*1.25)&(atlas[:,:,1]>atlas[:,:,0]*1.2)
    land = np.array(Image.fromarray((~water).astype('uint8')*255).resize((2048,2048),Image.Resampling.BOX),dtype=np.float32)/255
    rng = np.random.default_rng(noise['seed'])
    field = np.zeros((2048,2048),dtype=np.float32)
    for sigma,weight in noise['bands_master_pixels']:
        layer = rng.standard_normal((2048,2048),dtype=np.float32)
        if sigma:
            layer = gaussian_filter(layer,sigma)
        field += ((layer-layer.mean())/layer.std())*weight
    field = np.clip(field/field.std(),-noise['clip_standard_deviations'],noise['clip_standard_deviations'])
    if np.any(land>.99):
        field -= field[land>.99].mean()
    adjusted = terrain.copy()
    adjusted[:,:,:3] = np.clip(terrain[:,:,:3]*(1+field[:,:,None]*land[:,:,None]*noise['strength']),0,1)
    assert np.isfinite(adjusted).all()
    assert np.array_equal(adjusted[land==0],terrain[land==0])
    base = composite(terrain,corrected)
    final = composite(adjusted,corrected)
    opaque = corrected[:,:,3] == 1
    assert np.array_equal(np.array(base)[opaque],np.array(final)[opaque])
    final.save(out/'master.png')
    rgba(adjusted).save(out/'terrain_processed.png')
    rgba(corrected).save(out/'objects_processed.png')
    final.resize(tuple(entry['x2_size']),Image.Resampling.LANCZOS).save(out/'x2.png')
    openraster(out/'layers.ora',adjusted,corrected,final)
    if HERE==DEFAULT_HERE and entry['world']=='mm6' and entry['map']=='oute3.odm':
        assert sha(out/'x2.png') == noise['reference_sha256'], 'Approved New Sorpigal pixels drifted'
    scene = json.loads((out/'scene.json').read_text())
    overlay = Image.new('RGBA',tuple(entry['x2_size']))
    draw = ImageDraw.Draw(overlay)
    for model in scene['bmodels']:
        for face in model['faces']:
            if face['attributes']&0x2000 or len(face['vertex_indices'])<3:
                continue
            points = np.array([[model['vertices'][i][axis] for axis in 'xyz'] for i in face['vertex_indices']])
            if np.cross(points[1]-points[0],points[2]-points[0])[2] <= 0:
                continue
            xy = [((float(x)+32768)/65536*entry['x2_size'][0],
                   (32768-float(y))/65536*entry['x2_size'][1]) for x,y,z in points]
            draw.line(xy+[xy[0]],fill=(255,220,70,180),width=1)
    overlay.save(out/'geometry.png')
    report = dict(**entry,status='ready_for_authorized_acceptance', master_size=[2048,2048],
        outputs={n:sha(out/n) for n in ['x2.png','master.png','terrain_processed.png','objects_processed.png','layers.ora','geometry.png']},
        sources_sha256=sha(out/'sources.json'), capture_sha256=sha(out/'capture.json'),
        recipe_sha256=sha(HERE/'approved_recipe.json'),noise_sha256=sha(HERE/'approved_noise.json'),
        vertex_controls=capture['vertex_controls'],max_projection_error_x2_pixels=capture['max_projection_error_x2_pixels'],
        processed_object_alpha_exactly_preserved=True,open_water_unchanged_by_noise=True,geometry_moved=False,
        land_fraction=float(land.mean()), recipe='Gentler vinevi capture plus approved light land-only noise',
        limitations=['Static terrain and BModels; no sprite vegetation, actors or event-driven changes.',
                     'Native tile lookup and original world bounds; repeated water texture retained.'])
    save(out/'export.json',report)
    return report


def main():
    global HERE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--available',action='store_true',help='Process completed captures while rendering continues')
    parser.add_argument('--follow',action='store_true',help='Finish completed captures as the render batch produces them')
    parser.add_argument('--map')
    parser.add_argument('--workspace',type=Path,default=DEFAULT_HERE,help='Rendered revision directory')
    args=parser.parse_args()
    HERE=args.workspace.resolve()
    scope=json.loads((HERE/'scope.json').read_text())['records']
    if args.follow:
        while True:
            remaining=[r for r in scope if not (HERE/r['directory']/'export.json').exists()]
            if not remaining:
                break
            for entry in remaining:
                if (HERE/entry['directory']/'capture.json').exists():
                    finish(entry)
                    print('FINISHED',entry['world'],entry['map'],flush=True)
            progress=json.loads((HERE/'render_progress.json').read_text())
            assert progress['status'] != 'failed', progress
            time.sleep(2)
    records=[]
    for entry in scope:
        if args.map and args.map != Path(entry['map']).stem:
            continue
        out=HERE/entry['directory']
        if args.available and not (out/'capture.json').exists():
            continue
        if (out/'export.json').exists():
            report=json.loads((out/'export.json').read_text())
            assert report['recipe_sha256']==sha(HERE/'approved_recipe.json') and report['noise_sha256']==sha(HERE/'approved_noise.json')
            assert all(sha(out/n)==h for n,h in report['outputs'].items())
        else:
            report=finish(entry)
        records.append(report)
        print('FINISHED',entry['world'],entry['map'],flush=True)
    save(HERE/'exports.json',dict(count=len(records),expected=len(scope),records=records))
    for world in ['mm6','mm7','mm8']:
        rows=[r for r in records if r['world']==world]
        if not rows:
            continue
        cols=4; sheet=Image.new('RGB',(cols*300,((len(rows)+cols-1)//cols)*328),'#1c242b');draw=ImageDraw.Draw(sheet)
        for index,row in enumerate(rows):
            x,y=index%cols*300,index//cols*328
            im=Image.open(HERE/row['directory']/'x2.png').resize((296,296),Image.Resampling.LANCZOS)
            sheet.paste(im,(x+2,y+28));draw.text((x+5,y+6),row['map']+' - '+row['name'],fill='white')
        sheet.save(HERE/(world+'_overview.png'))


if __name__=='__main__':
    main()
