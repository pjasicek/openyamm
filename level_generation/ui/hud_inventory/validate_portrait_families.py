"""Check family coverage and every pasted diagnostic pixel, without asserting visual approval."""
from functools import lru_cache
import json
from pathlib import Path

from PIL import Image

from prepare_portrait_families import HERE, OUT, ROOT, digest, display_candidate, fitted_preview


@lru_cache(maxsize=12)
def image(path):
    with Image.open(path) as im:
        return im.convert('RGB')


def main():
    doc = json.loads((OUT / 'manifest.json').read_text())
    for path, expected in doc['input_hashes'].items():
        assert digest(path) == expected, f'Input drift: {path}'
    assert digest(HERE / 'checkpoint/state.json') == doc['canonical_state_sha256']
    for m in doc['raw_masters'].values():
        assert digest(m['raw']) == m['raw_sha256']
    table_rows = [l.split('\t') for l in (ROOT / 'assets_dev/engine/data_tables/character_data.txt')
                  .read_text().splitlines() if l.split('\t')[0].isdigit()]
    expected = {f[19].strip().lower() or f'pc{int(f[0]):02d}-' for f in table_rows}
    assert {f['prefix'] for f in doc['families']} == expected
    seen, slots, native_count, candidate_count = set(), 0, 0, 0
    for family in doc['families']:
        folder = OUT / family['path']
        pack = json.loads((folder / 'manifest.json').read_text())
        native_sheet = image(str(folder / 'native_x2.png'))
        candidate_sheet = image(str(folder / 'candidate_x2.png'))
        assert not pack['summary']['approved']
        for frame in pack['frames']:
            slots += 1
            key = (family['prefix'],frame['frame'])
            assert key not in seen
            seen.add(key)
            x,y,w,h = frame['sheet_rect']
            box = (x,y,x+w,y+h)
            if frame['source']:
                source = frame['source']
                assert source['restoration_active']
                path = ROOT / source['source_path']
                assert digest(path) == source['source_sha256']
                reference = image(str(path)).resize((w,h),Image.Resampling.NEAREST)
                assert native_sheet.crop(box).tobytes() == reference.tobytes(), key
                native_count += 1
            selected = frame['selected']
            for alternative in frame['alternatives']:
                if alternative['path']:
                    assert digest(alternative['path']) == alternative['sha256']
            if selected:
                assert not selected['accepted'] and not selected['mapping_verified']
                if selected['path']:
                    with Image.open(selected['path']) as im:
                        reference = display_candidate(im)
                    assert reference.size == (w,h)
                else:
                    bx,by,bw,bh = selected['raw_rect']
                    raw = image(selected['raw'])
                    assert bx >= 0 and by >= 0 and bx+bw <= raw.width and by+bh <= raw.height
                    reference = fitted_preview(raw.crop((bx,by,bx+bw,by+bh)),(w,h))
                assert candidate_sheet.crop(box).tobytes() == reference.tobytes(), key
                candidate_count += 1
        print(family['prefix'], 'verified', flush=True)
    assert slots == doc['summary']['slots']
    result = dict(families=len(expected),frame_slots=slots,native_frames=native_count,
                  candidate_previews=candidate_count,table_coverage=True,source_and_raw_hashes=True,
                  sheet_pixels_verified=True,canonical_state_unchanged=True,visual_approval=False)
    (OUT / 'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
