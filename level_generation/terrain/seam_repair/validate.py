"""Check legal map joins against local texture gradients, not duplicated edge pixels."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

from build import P, W, L, read, byte


def main(directory=P):
    P = Path(directory)
    out = P / 'runtime_x2/worlds/mm6/terrain_x2'
    tiles = {p.stem: read(p) for p in out.glob('*.png')}
    assert len(tiles) == 63
    assert all(a.shape[:2] == (256, 256) for a in tiles.values())
    grid = json.loads((W / 'corrected_map_cells.json').read_text())
    joins = set()
    for y, row in enumerate(grid):
        for x, name in enumerate(row):
            if x + 1 < len(row):
                joins.add((name, 'E', row[x + 1]))
            if y + 1 < len(grid):
                joins.add((name, 'S', grid[y + 1][x]))
    def composite(name, frame):
        a = tiles[name]
        if name == '6wtrtyl':
            return frame
        if a.shape[2] == 4:
            alpha = a[:, :, 3:] / 255
            return a[:, :, :3] * alpha + frame * (1 - alpha)
        return a
    checks = []
    for first, side, second in sorted(joins):
        values = []
        for f in range(14):
            frame = tiles[f'6hdwtr{f:03}']
            a, b = composite(first, frame), composite(second, frame)
            if side == 'S':
                a, b = a.transpose(1, 0, 2), b.transpose(1, 0, 2)
            across = float(np.sqrt(np.mean((a[:, -1] - b[:, 0]) ** 2)))
            near = np.concatenate([np.diff(a[:, -8:], axis=1), np.diff(b[:, :8], axis=1)], axis=1)
            local = float(np.sqrt(np.mean(near ** 2)))
            values.append(across / max(local, 1))
        checks.append({'a': first, 'side': side, 'b': second, 'max_gradient_ratio': max(values),
                       'pass': max(values) < 1.75})
    failures = [c for c in checks if not c['pass']]
    # Coverage is unchanged at authoring resolution; the shore RGB uses the same material everywhere.
    for path in (W / 'authoring/v1').glob('6wtrdr*.png'):
        assert np.array_equal(read(path)[:, :, 3], read(P / 'authoring' / path.name)[:, :, 3])
    report = json.loads((P / 'report.json').read_text())
    assert 0.8 < report['loop_step_ratio'] < 1.2
    assert all(0.8 < c['after_border_detail_ratio'] < 1.3 for c in report['detail'].values())
    # Assemble actual native shoreline contexts and a representative selection of land joins.
    cat = json.loads((W.parent / 'mm6_new_sorpigal/catalogue.json').read_text())
    shores = [t for t in cat['tiles'] if t['family'] == 'shoreline']
    sheet = Image.new('RGB', (4 * 384, 3 * 384))
    for i, tile in enumerate(shores):
        for y, row in enumerate(tile['context_tiles']):
            for x, name in enumerate(row):
                im = Image.fromarray(byte(composite(name, tiles['6hdwtr000']))).resize((128, 128))
                sheet.paste(im, (i % 4 * 384 + x * 128, i // 4 * 384 + y * 128))
    sheet.save(P / 'shore_contexts.png')
    result = {'unique_joins': len(joins), 'frames_per_join': 14, 'checks': checks, 'failures': failures,
              'files': report['files'],
              'shore_authoring_alpha_unchanged': True,
              'threshold': 'Boundary RMS gradient <1.75 times the neighbouring seven-pixel gradients.'}
    (P / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'joins': len(joins), 'failures': failures, 'worst': max(c['max_gradient_ratio'] for c in checks)}, indent=2))
    assert not failures


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=P)
    main(parser.parse_args().directory)
