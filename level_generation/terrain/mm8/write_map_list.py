"""Write the map coverage guide from the effective scene-aware inventory."""
import json

from common import P
from inventory import family


def main():
    inventory = json.loads((P / 'effective_inventory.json').read_text())
    titles = {r['id']: r['title'] for r in json.loads((P / 'inventory.json').read_text())['maps']}
    lines = ['# MM8 terrain map guide', '',
             'All14 outdoor maps use the same world terrain pack. Switching maps does not require reinstalling.',
             'Counts below come from the effective tile grid, including scene overrides.', '',
             '| Map | Asset filename | Used static textures | Terrain families |',
             '| --- | --- | ---: | --- |']
    for record in inventory['maps']:
        families = sorted({family(n) for n in record['tiles']})
        lines.append('| %s | `%s.odm` | %d | %s |' %
                     (titles[record['id']], record['id'], len(record['tiles']),
                      ', '.join(n.replace('_', ' ') for n in families)))
    lines += ['', 'Animation adds14 frames each for water, lava and tar, shared by the maps that use those liquids.',
              'The package preserves native map placement, including original incompatible corner/edge combinations.',
              'See `reports/native_join_audit.json` and `reports/native_contexts/visual_review.json` for that distinction.', '']
    (P / 'MAPS.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
