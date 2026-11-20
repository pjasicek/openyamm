"""Composite Blender calibration passes and create inspectable comparison exports."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0,str(BASE))
from processing import openraster


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    rows = []
    for row in json.loads((HERE/'scope.json').read_text())['records']:
        out = HERE/row['directory']
        if not (out/'capture.json').exists():
            continue
        capture = json.loads((out/'capture.json').read_text())
        assert all(sha(out/n)==h for n,h in capture['outputs'].items())
        assert capture['provenance']['prepared_sha256']==sha(out/'prepared.json')
        terrain = Image.open(out/'terrain_master.png').convert('RGBA')
        terrain.putalpha(255)
        objects = Image.open(out/'buildings_master.png').convert('RGBA')
        # Alpha-normalized small unsharp preserves transparent-edge color and the exact rendered silhouette.
        pixels = np.array(objects,dtype=np.float32)/255
        alpha = pixels[:,:,3:]
        blur = gaussian_filter(pixels[:,:,:3]*alpha,(1.2,1.2,0))/np.maximum(gaussian_filter(alpha,(1.2,1.2,0)),1e-6)
        pixels[:,:,:3] = np.clip(pixels[:,:,:3]+.25*(pixels[:,:,:3]-blur),0,1)
        objects = Image.fromarray(np.round(pixels*255).astype('uint8'))
        assert np.array_equal(np.array(objects)[:,:,3],np.array(Image.open(out/'buildings_master.png'))[:,:,3])
        master = Image.alpha_composite(terrain,objects).convert('RGB')
        master.save(out/'master.png')
        objects.save(out/'buildings_processed.png')
        master.resize(tuple(row['x2_size']),Image.Resampling.LANCZOS).save(out/'x2.png')
        openraster(out/'layers.ora',np.array(terrain,dtype=np.float32)/255,pixels,master,name=row['name']+' - shoreline calibration')
        comparison = Image.new('RGB',(1200,640),'#1c242b')
        draw = ImageDraw.Draw(comparison)
        for column,(path,title) in enumerate([(Path(row['source'])/'original.png','Native original'),(out/'x2.png','Blender shoreline / shading candidate')]):
            image = Image.open(path).convert('RGB').resize((596,596),Image.Resampling.NEAREST if column==0 else Image.Resampling.LANCZOS)
            comparison.paste(image,(column*600+2,40))
            draw.text((column*600+8,10),row['name']+' - '+title,fill='white')
        comparison.save(HERE/(row['world']+'_'+row['stem']+'_comparison.png'))
        record = dict(**row,outputs={n:sha(out/n) for n in ['x2.png','master.png','buildings_processed.png','layers.ora']},
                      capture_sha256=sha(out/'capture.json'),status='candidate_for_style_review',
                      processed_building_alpha_unchanged=True,
                      model_vertices_checked=capture['model_vertices_checked'],
                      max_projection_error_x2_pixels=capture['max_projection_error_x2_pixels'])
        (out/'export.json').write_text(json.dumps(record,indent=2)+'\n')
        rows.append(record)
        print('EXPORTED',row['world'],row['stem'],flush=True)
    (HERE/'exports.json').write_text(json.dumps(dict(count=len(rows),records=rows),indent=2)+'\n')


if __name__=='__main__':
    main()
