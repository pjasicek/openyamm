"""Use the existing strict item validator; add the scroll-specific one-material contract."""
import importlib.util
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
source = P.parent / 'items_wip_amulets_gauntlets_20261018/scripts/validate_items.py'
spec = importlib.util.spec_from_file_location('item_validation', source)
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)


def main():
    reports = []
    for entry in json.loads((P / 'audit.json').read_text()):
        if entry['status'] != 'rebuild':
            continue
        icon = entry['icon']
        path = P / 'work/finished' / f'scroll_{icon}_export.glb'
        report = validation.check(path, {'tris': 5000})
        assert report['materials'] == 1, report
        doc, binary = validation.winding.read_glb(path)
        assert len(doc['meshes'][0]['primitives']) == 1
        reports.append({'icon': icon, **report})
        print('VALID', icon, report['triangles'], report['closed_parts'])
    assert len(reports) == 9
    (P / 'review/validation.json').write_text(json.dumps(reports, indent=2) + '\n')


if __name__ == '__main__':
    main()
