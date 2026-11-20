"""Live MM6 raw-to-logical sampling gate shared by inventory and redo preparation."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def audit(project):
    manifest = json.loads((project / 'manifest.json').read_text())
    path = project / 'registration.json'
    if not path.exists():
        return dict(passed=False, issue='Missing raw-to-export registration', frames=[])
    registration = json.loads(path.read_text())
    front = json.loads((HERE / 'mm6_goblin/direct_front_final/manifest.json').read_text())
    rows = []
    for name in manifest['frames']:
        record = registration.get(name)
        if record is None:
            rows.append({'frame': name, 'batch': None, 'status': 'unresolved_provenance'})
            continue
        row = {'frame': name, 'batch': record['batch']}
        method = record.get('matte', {}).get('method', '')
        if method.startswith('exact native sparse/empty endpoint'):
            row['status'] = 'native_endpoint_preserved'
            row['native_visible_pixels'] = record['matte']['native_visible_pixels']
        elif record.get('source_checkpoint'):
            canonical = record.get('canonical_pixel_frame', name)
            scale = front['frames'][canonical]['registration']['uniform_logical_scale']
            row.update(sampling_x=1 / scale, sampling_y=1 / scale,
                       basis='inverse retained goblin front raw-to-logical registration scale')
        elif record.get('effective_sampling_xy'):
            sx, sy = record['effective_sampling_xy']
            row.update(sampling_x=sx, sampling_y=sy,
                       basis='raw-to-export sampling including integer output-size rounding')
        elif isinstance(record.get('scale'), (int, float)):
            row.update(sampling_x=2 / record['scale'], sampling_y=2 / record['scale'],
                       basis='2 / raw-to-2x registration scale')
        elif record.get('component_registration'):
            samples = []
            for part in record['component_registration']:
                box, size = part['clean_bounds'], part['physical_size']
                samples.append([2 * (box[2] - box[0]) / size[0],
                                2 * (box[3] - box[1]) / size[1]])
            row.update(sampling_x=min(s[0] for s in samples), sampling_y=min(s[1] for s in samples),
                       basis='minimum across separately registered Genie endpoint components')
        else:
            row['status'] = 'unresolved_provenance'
        if 'sampling_x' in row:
            row['status'] = ('below_2x' if min(row['sampling_x'], row['sampling_y']) < 2 - 1e-8
                             else 'at_least_2x_sampling')
        rows.append(row)
    return dict(schema_version=1, required_sampling=2,
                passed=bool(rows) and all(r['status'] in ('at_least_2x_sampling', 'native_endpoint_preserved')
                                          for r in rows), frames=rows)
