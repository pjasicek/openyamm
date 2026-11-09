"""Collect and hash grounded road movement evidence; emit sheets for visual inspection."""
import argparse
import json
from PIL import ImageDraw
from common import P, Image, np, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-complete', action='store_true')
    parser.add_argument('--stepping', action='store_true')
    args = parser.parse_args()
    stage_path = P / ('reports/road_extra_fixture_stage.json' if args.stepping
                      else 'reports/road_fixture_stage.json')
    stage = json.loads(stage_path.read_text())
    folder = P / 'fixtures/roads_v1/captures'
    output = P / 'fixtures/roads_v1/review'
    output.mkdir(exist_ok=True)
    results, pending = {}, []
    names = (list(stage['poses']) if args.stepping else
             ['flat_roads_' + family + '_' + side + '_x2'
              for family in ('dirt', 'grey') for side in ('west', 'east', 'south', 'north')])
    for pose_name in names:
        name = 'mm8_' + pose_name + '_walk'
        path = folder / (name + '.json')
        if not path.exists():
            pending.append(pose_name)
            continue
        meta = json.loads(path.read_text())
        if 'movement_samples' not in meta:
            pending.append(pose_name)
            continue
        assert meta['fixture_stage_sha256'] == sha(stage_path)
        assert meta['fixture_pose']['grounded']
        assert meta['movement_actions_sha256'] == sha(P / 'fixtures/roads_v1/movement_actions.json')
        assert len(meta['movement_samples']) == 13
        assert all(sha(folder / n) == h for n, h in meta['movement_samples'].items())
        sheet = Image.new('RGB', (1200, 660), '#202933')
        draw = ImageDraw.Draw(sheet)
        for k, suffix in enumerate(('walk_start', 'walk_02', 'walk_05', 'walk_08', 'walk_10', 'walk_11')):
            im = Image.open(folder / (name + '_' + suffix + '.png')).crop((200, 300, 1400, 930))
            x, y = k % 3 * 400, k // 3 * 330
            draw.text((x + 3, y + 3), pose_name + ' ' + suffix, fill='white')
            sheet.paste(im.resize((400, 300)), (x, y + 30))
        sheet_path = output / (pose_name + '_walk_samples.png')
        sheet.save(sheet_path)
        start = np.asarray(Image.open(folder / (name + '_walk_start.png')).crop((200, 300, 1400, 930)), float)
        end = np.asarray(Image.open(folder / (name + '_walk_11.png')).crop((200, 300, 1400, 930)), float)
        results[pose_name] = dict(metadata_sha256=sha(path), samples=meta['movement_samples'],
                                  sheet_sha256=sha(sheet_path), image_change_mae=float(abs(start - end).mean()))
    report = dict(status='awaiting_visual_review', results=results, pending=pending,
                  stage_sha256=sha(stage_path), script_sha256=sha(P / 'review_road_walks.py'),
                  scope='Grounded routes; twelve0.3-second forward steps each, sampled screenshots')
    (output / ('stepping_walks.json' if args.stepping else 'walks.json')).write_text(json.dumps(report, indent=2) + '\n')
    print('Collected', len(results), 'walks;', len(pending), 'pending')
    if args.require_complete:
        assert not pending, pending
        assert all(r['image_change_mae'] > 1 for r in results.values()), 'No visible movement'


if __name__ == '__main__':
    main()
