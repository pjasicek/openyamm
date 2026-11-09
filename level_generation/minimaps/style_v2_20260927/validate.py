"""Check calibration artifacts and distinguish unchanged geometry from intentionally rounded coastlines."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import label

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = BASE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    exports = read(HERE/'exports.json')
    assert exports['count']==4
    records = []
    for row in exports['records']:
        out = HERE/row['directory']
        prepared = read(out/'prepared.json')
        capture = read(out/'capture.json')
        assert sha(out/'capture.json')==row['capture_sha256']
        assert sha(HERE/'recipe.json')==prepared['recipe_sha256']
        assert sha(out/'prepared.json')==capture['provenance']['prepared_sha256']
        assert sha(HERE/'render.py')==capture['provenance']['script_sha256']
        assert sha(Path(row['source'])/'scene.blend')==prepared['source_scene_sha256']
        assert sha(Path(row['source'])/'scene.json')==prepared['source_data_sha256']
        for filename,expected in {**row['outputs'],**capture['outputs'],**prepared['masks']}.items():
            assert sha(out/filename)==expected,filename
        for texture in prepared['textures'].values():
            assert sha(texture['path'])==texture['sha256']
            assert sha(texture['source'])==texture['source_sha256']
        for filename,expected in prepared['water_mask_sources'].items():
            assert sha(filename)==expected
        candidate = Image.open(out/'x2.png')
        assert candidate.format=='PNG' and candidate.mode=='RGB' and list(candidate.size)==row['x2_size']
        assert Image.open(out/'master.png').size==(2048,2048)
        assert capture['terrain_vertices_unchanged'] and capture['max_projection_error_x2_pixels']==0
        assert np.array_equal(np.array(Image.open(out/'buildings_master.png'))[:,:,3],
                              np.array(Image.open(out/'buildings_processed.png'))[:,:,3])
        components = []
        for filename in ['water_original_mask.png','water_mask.png']:
            mask = np.array(Image.open(out/filename))>127
            labs,count = label(mask)
            components.append(int((np.bincount(labs.ravel())[1:]>256).sum()))
        records.append(dict(world=row['world'],map=row['stem'],model_vertices=row['model_vertices_checked'],
            geometry_projection_error_x2_pixels=0,shore_max_boundary_distance_x2_pixels=row['shoreline_max_boundary_distance_x2_pixels'],
            water_components_before_after=components,x2_size=row['x2_size']))
    accepted = read(BASE/'accepted.json')['records']
    assert len(accepted)==42
    for target,record in accepted.items():
        assert sha(ROOT/record['runtime_output_path'])==record['sha256'],target
        assert sha(record['artifact'])==record['sha256'],target
    report = dict(result='PASS',count=4,exports_sha256=sha(HERE/'exports.json'),records=records,
        model_vertices_checked=sum(r['model_vertices'] for r in records),max_geometry_projection_error_x2_pixels=0,
        max_shore_boundary_distance_x2_pixels=max(r['shore_max_boundary_distance_x2_pixels'] for r in records),
        accepted_and_runtime_minimaps_unchanged=42,
        note='Geometry remains fixed. The coastal mask deliberately changes within the reported tolerance; this is not a claim of exact painted-silhouette equivalence.')
    (HERE/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
