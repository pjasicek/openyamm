"""Render every failing native join in original/enhanced map context, without changing map placement."""
import json
from PIL import ImageDraw
from common import P, Image, seams, sha
from audit_native_joins import load_inputs


def main():
    current, original, grids = load_inputs()
    audit_path = P / 'reports/native_join_audit.json'
    audit = json.loads(audit_path.read_text())
    folder = P / 'reports/native_contexts'
    folder.mkdir(exist_ok=True)
    rows, files = [], {}
    # Twelve cases per page, each original/current pair at native-scale context.
    for page in range((len(audit['failures']) + 11) // 12):
        sheet = Image.new('RGB', (1536, 4 * 300), '#202933')
        draw = ImageDraw.Draw(sheet)
        for index, case in enumerate(audit['failures'][page * 12:page * 12 + 12]):
            example = case['example'];grid = grids[example['map']]
            y, x = example['row'], example['col']
            # A3x3 window includes the failing join and its immediate neighbours.
            top, left = min(max(y - 1, 0), 124), min(max(x - 1, 0), 124)
            base_x, base_y = index % 3 * 512, index // 3 * 300
            label = '%s %s %s | %s r%d c%d' % (case['a'], case['side'], case['b'], example['map'], y, x)
            draw.text((base_x + 3, base_y + 3), label, fill='white')
            draw.text((base_x + 3, base_y + 18), 'native left / enhanced right', fill='white')
            for panel, tiles in enumerate((original, current)):
                context = Image.new('RGB', (768, 768))
                for dy in range(3):
                    for dx in range(3):
                        context.paste(Image.fromarray(seams.byte(tiles[grid[top + dy][left + dx]])), (dx * 256, dy * 256))
                sheet.paste(context.resize((256, 256)), (base_x + panel * 256, base_y + 40))
            rows.append(dict(page=page, slot=index, **case))
        path = folder / ('page_%02d.png' % page)
        sheet.save(path);files[path.name] = sha(path)
    report = dict(status='awaiting_visual_review', scope='All metric-failing phase0 native adjacencies, original/current3x3 context',
                  cases=rows, pages=files, audit_sha256=sha(audit_path),
                  candidate_stage_sha256=sha(P / 'reports/candidate_stage.json'),
                  script_sha256=sha(P / 'review_native_contexts.py'))
    (folder / 'index.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Prepared', len(rows), 'cases on', len(files), 'pages')


if __name__ == '__main__':
    main()
